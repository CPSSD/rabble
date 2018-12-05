package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
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

type usersResponse struct {
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
		var jsonResp usersResponse
		err := decoder.Decode(&req)
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		if err != nil {
			log.Printf("Invalid JSON, error: %v\n", err)
			w.WriteHeader(http.StatusBadRequest)
			jsonResp.Error = "Invalid JSON"
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
		}
		enc.Encode(jsonResp)
	}
}
