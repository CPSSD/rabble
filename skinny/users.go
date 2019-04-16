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

	pb "github.com/cpssd/rabble/services/proto"
)

const (
	couldNotLoadProfilePic = "Could not load profile pic from request"
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
	UserID  int64  `json:"user_id"`
}

// handleLogin sends an RPC to the users service to check if a login
// is correct.
func (s *serverWrapper) handleLogin() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var t loginStruct
		var jsonResp userResponse
		jsonResp.Success = false
		enc := json.NewEncoder(w)

		err := decoder.Decode(&t)
		if err != nil {
			log.Println(invalidJSONError)
			log.Printf("Error: %s\n", err)
			jsonResp.Error = invalidJSONError
			w.WriteHeader(http.StatusBadRequest)
			enc.Encode(jsonResp)
			return
		}
		lr := &pb.LoginRequest{
			Handle:   t.Handle,
			Password: t.Password,
		}
		ctx, cancel := context.WithTimeout(context.Background(), defaultTimeoutDuration)
		defer cancel()

		resp, err := s.users.Login(ctx, lr)
		if err != nil {
			log.Println(err)
			jsonResp.Error = "Issue with handling login request"
			w.WriteHeader(http.StatusInternalServerError)
			enc.Encode(jsonResp)
			return
		}
		if resp.Result == pb.LoginResponse_ACCEPTED {
			session, err := s.store.Get(r, "rabble-session")
			if err != nil {
				log.Println(err)
				jsonResp.Error = "Issue with handling login request"
				w.WriteHeader(http.StatusInternalServerError)
				enc.Encode(jsonResp)
				return
			}
			log.Printf("User %d login success: %t", resp.GlobalId, jsonResp.Success)
			jsonResp.Success = true
			jsonResp.UserID = resp.GlobalId

			session.Values["handle"] = t.Handle
			session.Values["global_id"] = resp.GlobalId
			session.Values["display_name"] = resp.DisplayName
			session.Save(r, w)
		} else if resp.Result == pb.LoginResponse_DENIED {
			w.WriteHeader(http.StatusUnauthorized)
		} else {
			w.WriteHeader(http.StatusInternalServerError)
		}

		w.Header().Set("Content-Type", "application/json")
		// Intentionally not revealing to the user if an error occurred.
		enc.Encode(jsonResp)
	}
}

// Clears the user's session when called.
func (s *serverWrapper) handleLogout() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		session, err := s.store.Get(r, "rabble-session")
		var jsonResp userResponse
		jsonResp.Success = false
		enc := json.NewEncoder(w)
		if err != nil {
			fmt.Println(err)
			jsonResp.Error = "Issue with handling logout request"
			w.WriteHeader(http.StatusInternalServerError)
			enc.Encode(jsonResp)
			return
		}
		session.Options.MaxAge = -1 // Marks the session for deletion.
		err = session.Save(r, w)
		if err != nil {
			fmt.Println(err)
			jsonResp.Error = "Issue with handling logout request"
			w.WriteHeader(http.StatusInternalServerError)
			enc.Encode(jsonResp)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		jsonResp.Success = true
		enc.Encode(jsonResp)
	}
}

// handleRegister sends an RPC to the users service to create a user with the
// given info.
func (s *serverWrapper) handleRegister() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var req registerRequest
		var jsonResp userResponse
		jsonResp.Success = false
		err := decoder.Decode(&req)
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		if err != nil {
			log.Printf(invalidJSONErrorWithPrint, err)
			w.WriteHeader(http.StatusBadRequest)
			jsonResp.Error = invalidJSONError
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
		ctx, cancel := context.WithTimeout(context.Background(), defaultTimeoutDuration)
		defer cancel()

		resp, err := s.users.Create(ctx, u)
		if err != nil {
			log.Printf("could not add new user: %v", err)
			jsonResp.Error = "Error communicating with create user service"
			w.WriteHeader(http.StatusInternalServerError)
		} else if resp.ResultType != pb.CreateUserResponse_OK {
			log.Printf("Error creating user: %s", resp.Error)
			jsonResp.Error = resp.Error
			w.WriteHeader(http.StatusInternalServerError)
		} else {
			session, err := s.store.Get(r, "rabble-session")
			if err != nil {
				log.Printf("Error getting session store after create: %s", err)
				jsonResp.Error = "Issue with login after create\n"
				w.WriteHeader(http.StatusInternalServerError)
			} else {
				jsonResp.UserID = resp.GlobalId
				jsonResp.Success = true
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
		resp.Success = false

		enc := json.NewEncoder(w)

		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Call to update user by not logged in user")
			w.WriteHeader(http.StatusForbidden)
			resp.Error = invalidJSONError
			enc.Encode(resp)
			return
		}

		err = decoder.Decode(&req)
		if err != nil {
			log.Printf(invalidJSONErrorWithPrint, err)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = invalidJSONError
			enc.Encode(resp)
			return
		}

		// This makes the handle optional to send, since it's already
		// provided by the session handler.
		req.Handle = handle

		log.Printf("Trying to update user %#v.\n", req.Handle)
		ctx, cancel := context.WithTimeout(context.Background(), defaultTimeoutDuration)
		defer cancel()

		updateResp, err := s.users.Update(ctx, &req)

		if err != nil {
			log.Printf("Could not update user: %v", err)
			resp.Error = "Error communicating with user update service"
			w.WriteHeader(http.StatusInternalServerError)
		} else if updateResp.Result != pb.UpdateUserResponse_ACCEPTED {
			// Unlike in user response, we will be clear that they
			// provided an incorrect password.
			log.Printf("Error updating user: %s", resp.Error)
			resp.Error = updateResp.Error
			w.WriteHeader(http.StatusInternalServerError)
		} else {
			log.Print("Update session display_name if it changed")
			resp.Success = true
		}

		enc.Encode(resp)
	}
}

func (s *serverWrapper) getProfilePicPath(userID int64) string {
	filename := fmt.Sprintf("user_%d", userID)
	filepath := path.Join(staticAssets, filename)
	return filepath
}

func (s *serverWrapper) handleUserUpdateProfilePic() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var resp userResponse
		resp.Success = false
		enc := json.NewEncoder(w)
		w.Header().Set("Content-Type", "application/json")

		userID, err := s.getSessionGlobalID(r)
		if err != nil {
			log.Printf("Call to update user by not logged in user")
			w.WriteHeader(http.StatusForbidden)
			resp.Error = invalidJSONError
			enc.Encode(resp)
			return
		}

		image, _, err := r.FormFile("profile_pic")
		defer image.Close()
		if err != nil {
			log.Printf(couldNotLoadProfilePic+": %v", err)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = couldNotLoadProfilePic
			enc.Encode(resp)
			return
		}
		buf := bytes.NewBuffer(nil)
		if _, err := io.Copy(buf, image); err != nil {
			log.Printf("Error copying image to buffer: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = couldNotLoadProfilePic
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
			enc.Encode(resp)
			return
		}
		filepath := s.getProfilePicPath(userID)
		log.Printf("Writing image to %s", filepath)
		if err := ioutil.WriteFile(filepath, buf.Bytes(), 0644); err != nil {
			log.Printf("Error writing file to %s: %v", filepath, err)
			w.WriteHeader(http.StatusBadRequest)
			resp.Error = "Error writing image to disk"
			enc.Encode(resp)
			return
		}
		resp.Success = true
		enc.Encode(resp)
	}
}
