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
	"strings"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/gorilla/mux"
)

type activity struct {
	Type string `json:"type"`
}

// handleActorInbox is where server to server actions that relate to activities
// are sent. It routes them using routeActivity to the correct handler.
//
// See https://www.w3.org/TR/activitypub/#inbox for details in the spec
//
// Specifically things modifying Actor collections are routed here.
// See routes.go to view the activity routing in actorInboxRouter
func (s *serverWrapper) handleActorInbox() http.HandlerFunc {
	const (
		inboxErr  = "Error handling actor inbox for '%#v': %s: %v"
		typeField = "could not parse type field"
		notFound  = "unable to handle given activity type"
	)

	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]

		// We're reading from a stream, so we need to ensure it will
		// get passed downwards without hitting EOF. We create another
		// Reader and pass that onwards instead.
		var newStream bytes.Buffer
		body := io.TeeReader(r.Body, &newStream)

		d := json.NewDecoder(body)
		var a activity

		if err := d.Decode(&a); err != nil {
			log.Printf(inboxErr, recipient, typeField, err)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON-LD: %v.", typeField)
			return
		}

		if s.actorInboxRouter == nil || len(s.actorInboxRouter) == 0 {
			log.Fatalf("Actor inbox not initalized, can not continue.")
		}

		m, exists := s.actorInboxRouter[strings.ToLower(a.Type)]
		if !exists {
			log.Printf(inboxErr, recipient, notFound, a.Type)
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintf(w, "Could not handle activity '%#v': %v.",
				a.Type, notFound)
			return
		}

		r.Body = ioutil.NopCloser(&newStream)
		m(w, r)
	}
}

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
		err := decoder.Decode(&t)
		if err != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", err)
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

type likeActorStruct struct {
	Id   string `json:"id"`
	Type string `json:"type"`
}

type likeActivityStruct struct {
	Actor   likeActorStruct `json:"actor"`
	Context string          `json:"@context"`
	Object  string          `json:"object"`
	Type    string          `json:"type"`
}

func (s *serverWrapper) handleLikeActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a like activity.\n", recipient)

		// TODO(iandioch, sailslick, CianLR): Parse JSON-LD in other shapes.
		decoder := json.NewDecoder(r.Body)
		var t likeActivityStruct
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		f := &pb.ReceivedLikeDetails{
			LikedObject: t.Object,
			LikerId: t.Actor.Id,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sLike.ReceiveLikeActivity(ctx, f)
		if err != nil || resp.ResultType == pb.LikeResponse_ERROR {
			if err != nil {
				log.Printf("Could not receive like activity. Error: %v", err)
			} else {
				log.Printf("Could not receive like activity. Error: %v",
						   resp.Error);
			}
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving like activity.\n")
			return
		}

		log.Println("Like activity received successfully.")
		fmt.Fprintf(w, "{}\n")
	}
}

