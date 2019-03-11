package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"path"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
)

const (
	invalidJSONError = "Invalid JSON"
)

type loginStruct struct {
	Handle   string `json:"handle"`
	Password string `json:"password"`
}

type registerRequest struct {
	Handle      string `json:"handle"`
	Password    string `json:"password"`
	DisplayName string `json:"displayName"`
	Bio         string `json:"bio"`
}

type userResponse struct {
	Error   string `json:"error"`
	Success bool   `json:"success"`
}

// handleLogin sends an RPC to the users service to check if a login
// is correct.
func (s *serverWrapper) handleLogin() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var t loginStruct
		err := decoder.Decode(&t)
		if err != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", err)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}
		lr := &pb.LoginRequest{
			Handle:   t.Handle,
			Password: t.Password,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.users.Login(ctx, lr)
		if err != nil {
			log.Println(err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with handling login request\n")
			return
		}
		if resp.Result == pb.LoginResponse_ACCEPTED {
			session, err := s.store.Get(r, "rabble-session")
			if err != nil {
				log.Println(err)
				w.WriteHeader(http.StatusInternalServerError)
				fmt.Fprintf(w, "Issue with handling login request\n")
				return
			}
			session.Values["handle"] = t.Handle
			session.Values["global_id"] = resp.GlobalId
			session.Values["display_name"] = resp.DisplayName
			session.Save(r, w)
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		success := resp.Result == pb.LoginResponse_ACCEPTED
		log.Printf("User %s login success: %t", t.Handle, success)
		// Intentionally not revealing to the user if an error occurred.
		err = enc.Encode(map[string]bool{
			"success": success,
		})
	}
}

// Clears the user's session when called.
func (s *serverWrapper) handleLogout() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		session, err := s.store.Get(r, "rabble-session")
		if err != nil {
			fmt.Println(err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with handling logout request\n")
			return
		}
		session.Options.MaxAge = -1 // Marks the session for deletion.
		err = session.Save(r, w)
		if err != nil {
			fmt.Println(err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with handling logout request\n")
			return
		}
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		err = enc.Encode(map[string]bool{
			"success": true,
		})
	}
}

// handleRegister sends an RPC to the users service to create a user with the
// given info.
func (s *serverWrapper) handleRegister() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var req registerRequest
		var jsonResp userResponse
		err := decoder.Decode(&req)
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		if err != nil {
			log.Printf("Invalid JSON, error: %v\n", err)
			w.WriteHeader(http.StatusBadRequest)
			jsonResp.Error = invalidJSONError
			jsonResp.Success = false
			enc.Encode(jsonResp)
			return
		}
		log.Printf("Trying to add new user %#v.\n", req.Handle)
		u := &pb.CreateUserRequest{
			DisplayName: req.DisplayName,
			Handle:      req.Handle,
			Password:    req.Password,
			Bio:         req.Bio,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.users.Create(ctx, u)
		jsonResp.Success = true
		if err != nil {
			log.Printf("could not add new user: %v", err)
			jsonResp.Error = "Error communicating with create user service"
			jsonResp.Success = false
		} else if resp.ResultType != pb.CreateUserResponse_OK {
			log.Printf("Error creating user: %s", resp.Error)
			jsonResp.Error = resp.Error
			jsonResp.Success = false
		} else {
			session, err := s.store.Get(r, "rabble-session")
			if err != nil {
				log.Printf("Error getting session store after create: %s", err)
				jsonResp.Error = "Issue with login after create\n"
				jsonResp.Success = false
			} else {
				session.Values["handle"] = req.Handle
				session.Values["global_id"] = resp.GlobalId
				session.Values["display_name"] = req.DisplayName
				session.Save(r, w)
			}
		}
		enc.Encode(jsonResp)
	}
}

// handleUserUpdate sends an RPC to the users service to update a user with the
// given info.
func (s *serverWrapper) handleUserUpdate() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		w.Header().Set("Content-Type", "application/json")

		var (
			req  pb.UpdateUserRequest
			resp userResponse
		)

		enc := json.NewEncoder(w)

		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Call to update user by not logged in user")
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = invalidJSONError
			resp.Success = false
			enc.Encode(resp)
			return
		}

		err = decoder.Decode(&req)
		if err != nil {
			log.Printf("Invalid JSON, error: %v\n", err)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = invalidJSONError
			resp.Success = false
			enc.Encode(resp)
			return
		}

		// This makes the handle optional to send, since it's already
		// provided by the session handler.
		req.Handle = handle

		log.Printf("Trying to update user %#v.\n", req.Handle)
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		updateResp, err := s.users.Update(ctx, &req)
		resp.Success = true

		if err != nil {
			log.Printf("Could not update user: %v", err)
			resp.Error = "Error communicating with user update service"
			resp.Success = false
		} else if updateResp.Result != pb.UpdateUserResponse_ACCEPTED {
			// Unlike in user response, we will be clear that they
			// provided an incorrect password.
			log.Printf("Error updating user: %s", resp.Error)
			resp.Error = updateResp.Error
			resp.Success = false
		} else {
			log.Print("Update session display_name if it changed")
			resp.Success = true
		}

		enc.Encode(resp)
	}
}

func (s *serverWrapper) handleUserUpdateProfilePic() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var resp userResponse
		enc := json.NewEncoder(w)
		w.Header().Set("Content-Type", "application/json")

		user_id, err := s.getSessionGlobalId(r)
		if err != nil {
			log.Printf("Call to update user by not logged in user")
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = invalidJSONError
			resp.Success = false
			enc.Encode(resp)
			return
		}

		image, _, err := r.FormFile("profile_pic")
		defer image.Close()
		if err != nil {
			log.Printf("Could not load profile pic from request: %v", err);
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = "Could not load profile pic from request"
			resp.Success = false
			enc.Encode(resp)
			return
		}
		buf := bytes.NewBuffer(nil)
		if _, err := io.Copy(buf, image); err != nil {
			log.Printf("Error copying image to buffer: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = "Could not load profile pic from request"
			resp.Success = false
			enc.Encode(resp)
			return
		}
		allowedTypes := []string{
			"image/gif",
			"image/jpeg",
			"image/png",
			"image/webp",
		}
		detectedType := http.DetectContentType(buf.Bytes())
		found := false
		for _, t := range allowedTypes {
			if detectedType == t {
				found = true
				break
			}
		}
		if !found {
			log.Printf("Type dissallowed: %v", detectedType)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = "Upload is not of an allowed type"
			resp.Success = false
			enc.Encode(resp)
			return
		}
		filename := fmt.Sprintf("user_%d", user_id)
		filepath := path.Join(staticAssets, filename)
		log.Printf("Writing image to %s", filepath)
		if err := ioutil.WriteFile(filepath, buf.Bytes(), 0644); err != nil {
			log.Printf("Error writing file to %s: %v", filepath, err)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = "Error writing image to disk"
			resp.Success = false
			enc.Encode(resp)
			return
		}
		resp.Success = true
		enc.Encode(resp)
	}
}
