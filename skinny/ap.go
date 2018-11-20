package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	pb "github.com/cpssd/rabble/services/proto/gopb"
	"github.com/gorilla/mux"
)

type createActivityObjectStruct struct {
	Content      string   `json:"content"`
	Name         string   `json:"name"`
	Published    string   `json:"published"`
	AttributedTo string   `json:"attributedTo"`
	Recipient    []string `json:"to"`
	Type         string   `json:"type"`
}

type createActivityStruct struct {
	Actor     string                     `json:"actor"`
	Context   string                     `json:"@context"`
	Object    createActivityObjectStruct `json:"object"`
	Recipient []string                   `json:"to"`
	Type      string                     `json:"type"`
}

type followActivityStruct struct {
	Actor     string   `json:"actor"`
	Context   string   `json:"@context"`
	Object    string   `json:"object"`
	Recipient []string `json:"to"`
	Type      string   `json:"type"`
}

func (s *serverWrapper) handleCreateActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]

		log.Printf("User %v received a create activity\n", recipient)

		// TODO (sailslick) Parse jsonLD in general case
		decoder := json.NewDecoder(r.Body)
		var t createActivityStruct
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		protoTimestamp, parseErr := parseTimestamp(w, t.Object.Published)
		if parseErr != nil {
			log.Println(parseErr)
			return
		}

		nfa := &pb.NewForeignArticle{
			AttributedTo: t.Object.AttributedTo,
			Content:      t.Object.Content,
			Published:    protoTimestamp,
			Recipient:    recipient,
			Title:        t.Object.Name,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.create.ReceiveCreate(ctx, nfa)
		if err != nil || resp.ResultType == pb.CreateResponse_ERROR {
			log.Printf("Could not receive create activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving create activity\n")
			return
		}

		log.Printf("Activity was alright :+1:Received: %v\n", resp.Error)
		fmt.Fprintf(w, "Created blog with title\n")
	}
}

func (s *serverWrapper) handleFollowActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a follow activity.\n", recipient)

		// TODO(iandioch, sailslick): Parse JSON-LD in other shapes.
		decoder := json.NewDecoder(r.Body)
		var t followActivityStruct
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		f := &pb.ReceivedFollowDetails{
			Follower: t.Actor,
			Followed: t.Object,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sFollow.ReceiveFollowActivity(ctx, f)
		if err != nil ||
			resp.ResultType == pb.FollowActivityResponse_ERROR {
			log.Printf("Could not receive follow activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving follow activity.\n")
			return
		}

		log.Println("Activity received successfully.")
		fmt.Fprintf(w, "{}\n")
	}
}
