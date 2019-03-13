package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
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

		buf := new(bytes.Buffer)
		buf.ReadFrom(r.Body)
		body := buf.String()

		d := json.NewDecoder(strings.NewReader(body))
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

		// We're reading from a stream, so we need to ensure it will
		// get passed downwards without hitting EOF. We create another
		// Reader and pass that onwards instead.
		r.Body = ioutil.NopCloser(strings.NewReader(body))
		m(w, r)
	}
}

type ImageObject struct {
	Type string `json:"type"`
	Url  string `json:"url"`
}

type KeyObject struct {
    Id                string       `json:"id"`
    Owner             string       `json:"owner"`
    PublicKeyPem      string       `json:"publicKeyPem"`
}

type ActorObjectStruct struct {
	// The @context in the output JSON-LD
	Context           []string     `json:"@context"`

	// The same types as the protobuf ActorObject.
	Type              string       `json:"type"`
	Inbox             string       `json:"inbox"`
	Outbox            string       `json:"outbox"`
	Name              string       `json:"name"`
	PreferredUsername string       `json:"preferredUsername"`
	Icon              *ImageObject `json:"icon,omitempty"`
	Followers         string       `json:followers`
	Following         string       `json:following`
    PublicKey         *KeyObject   `json:"publicKey"`
}

func (s *serverWrapper) handleActor() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		u := v["username"]
		req := &pb.ActorRequest{
			Username: u,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.actors.Get(ctx, req)
		if err != nil {
			log.Printf("Could not receive return actor object. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create actor object.\n")
			return
		}
		if resp.Actor == nil {
			log.Printf("Actors service Get returned nil actor\n")
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create actor object.\n")
			return
		}

        context := []string{
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
        }

		// Unfortunately, there's no easier way to add a field to a struct.
		actor := &ActorObjectStruct{
			Context:           context,
			Type:              resp.Actor.Type,
			Inbox:             resp.Actor.Inbox,
			Outbox:            resp.Actor.Outbox,
			Name:              resp.Actor.Name,
			PreferredUsername: resp.Actor.PreferredUsername,
			Followers:         resp.Actor.Followers,
			Following:         resp.Actor.Following,
		}

        actor.PublicKey = &KeyObject{
            Id:             resp.Actor.PublicKey.Id,
            Owner:          resp.Actor.PublicKey.Owner,
            PublicKeyPem:   resp.Actor.PublicKey.PublicKeyPem,
        }

		filepath := s.getProfilePicPath(resp.Actor.GlobalId)
		if _, err := os.Stat(filepath); err == nil {
			// Profile pic exists
			actor.Icon = &ImageObject{
				Type: "Image",
				Url: fmt.Sprintf(
					"http://%s/assets/user_%d",
					s.hostname, resp.Actor.GlobalId),
			}
		}

		enc := json.NewEncoder(w)
		err = enc.Encode(actor)
		if err != nil {
			log.Printf("Could not marshal Actor object. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create actor object.\n")
			return
		}
		log.Printf("Created actor successfully.")
	}
}

func (s *serverWrapper) handleFollowingCollection() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		u := v["username"]
		req := &pb.ActorRequest{Username: u}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.actors.GetFollowing(ctx, req)
		if err != nil {
			log.Printf("Could not create following collection object. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create following collection object.\n")
			return
		}
		if resp.Collection == "" {
			log.Printf("Actors service GetFollowing returned empty string\n")
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create following collection object.\n")
			return
		}

		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, resp.Collection)
		log.Printf("Created following collection successfully.")
	}
}

func (s *serverWrapper) handleFollowersCollection() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		u := v["username"]
		req := &pb.ActorRequest{Username: u}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.actors.GetFollowers(ctx, req)
		if err != nil {
			log.Printf("Could not create followers collection object. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create followers collection object.\n")
			return
		}
		if resp.Collection == "" {
			log.Printf("Actors service GetFollowers returned empty string\n")
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create followers collection object.\n")
			return
		}

		w.Header().Set("Content-Type", "application/json")
	}
}

type createActivityObjectStruct struct {
	Content      string   `json:"content"`
	Name         string   `json:"name"`
	Published    string   `json:"published"`
	AttributedTo string   `json:"attributedTo"`
	Recipient    []string `json:"to"`
	Type         string   `json:"type"`
	Id           string   `json:"id"`
	URL          string   `json:"url"`
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

		// TODO: Parse jsonLD in general case
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

		protoTimestamp, parseErr := parseTimestamp(w, t.Object.Published, false)
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
			Id:           t.Object.Id,
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

		// TODO: Parse JSON-LD in other shapes.
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
			LikerId:     t.Actor.Id,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sLike.ReceiveLikeActivity(ctx, f)
		if err != nil {
			log.Printf("Could not receive like activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving like activity.\n")
			return
		} else if resp.ResultType == pb.LikeResponse_ERROR {
			log.Printf("Could not receive like activity. Error: %v",
				resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving like activity.\n")
			return
		}

		log.Println("Like activity received successfully.")
		fmt.Fprintf(w, "{}\n")
	}
}

type approvalObject struct {
	Actor  string `json:"actor"`
	Object string `json:"object"`
	Type   string `json:"type"`
}

type approvalActivity struct {
	Actor     string         `json:"actor"`
	Context   string         `json:"@context"`
	Object    approvalObject `json:"object"`
	Recipient []string       `json:"to"`
	Type      string         `json:"type"`
}

func (s *serverWrapper) handleApprovalActivity() http.HandlerFunc {
	const (
		nonFollow  = "Received %s activity of type %s, only support follow.\n"
		receiveErr = "Could not receive %s activity: %v"
	)
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received an approval activity.\n", recipient)

		// TODO: Parse JSON-LD in other shapes.
		decoder := json.NewDecoder(r.Body)
		var t approvalActivity
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		// Lowercase any types do string comparisons against
		t.Type = strings.ToLower(t.Type)
		t.Object.Type = strings.ToLower(t.Object.Type)

		if t.Object.Type != "follow" {
			log.Printf(nonFollow, t.Type, t.Object.Type)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, nonFollow, t.Type, t.Object.Type)
			return
		}

		ap := &pb.ReceivedApproval{
			Follow: &pb.ReceivedFollowDetails{
				Follower: t.Object.Actor,
				Followed: t.Object.Object,
			},
			// We know type is either an accept or reject activity
			// since the request was routed here.
			Accept: t.Type == "accept",
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.approver.ReceiveApproval(ctx, ap)
		if err != nil {
			log.Printf(receiveErr, t.Type, err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Error handling %s activity.\n", t.Type)
		} else if resp.ResultType == pb.ApprovalResponse_ERROR {
			log.Printf(receiveErr, t.Type, resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Error handling %s activity.\n", t.Type)
			return
		}
		log.Println("Activity received successfully.")
		fmt.Fprintf(w, "{}\n")
	}
}

type deleteActivity struct {
	Context string   `json:"@context"`
	Object  activity `json:"object"`
	Type    string   `json:"type"`
}

func (s *serverWrapper) handleDeleteActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a delete activity.\n", recipient)

		// Pass control to corresponding delete type
		buf := new(bytes.Buffer)
		buf.ReadFrom(r.Body)
		body := buf.String()

		d := json.NewDecoder(strings.NewReader(body))
		var del deleteActivity

		if err := d.Decode(&del); err != nil {
			log.Printf("Could not decode Delete activity: %#v", err)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Could not decode Delete activity")
			return
		}

		if s.deleteActivityRouter == nil || len(s.deleteActivityRouter) == 0 {
			log.Fatalf("Delete router not initalized, can not continue.")
		}

		// Similarily to the actorInboxRouter different functions are called
		// depending on the type of the object to be deleted.
		m, exists := s.deleteActivityRouter[strings.ToLower(del.Object.Type)]
		if !exists {
			log.Printf("Could not find delete handle for object of type %#v",
				del.Object.Type)
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintf(w, "Could not handle Delete activity for '%#v'",
				del.Object.Type)
			return
		}

		// We're reading from a stream, so we need to ensure it will
		// get passed downwards without hitting EOF. We create another
		// Reader and pass that onwards instead.
		r.Body = ioutil.NopCloser(strings.NewReader(body))
		m(w, r)
	}
}

type likeDeleteActivity struct {
	Context string             `json:"@context"`
	Object  likeActivityStruct `json:"object"`
	Type    string             `json:"type"`
}

func (s *serverWrapper) handleLikeDeleteActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a like Delete activity.\n", recipient)

		decoder := json.NewDecoder(r.Body)
		var t likeDeleteActivity

		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		f := &pb.ReceivedLikeDeleteDetails{
			LikedObjectApId: t.Object.Object,
			LikingUserApId:  t.Object.Actor.Id,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sDelete.ReceiveLikeDeleteActivity(ctx, f)
		if err != nil {
			log.Printf("Could not receive like delete activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving like delete activity.\n")
			return
		} else if resp.ResultType == pb.DeleteResponse_ERROR {
			log.Printf("Could not receive like delete activity. Error: %v",
				resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving like delete activity.\n")
			return
		}

		log.Println("Like delete activity received successfully.")
		fmt.Fprintf(w, "{}\n")
	}
}

// TODO(sailslick): Properly fill in announce structs
type announceActor struct {
	Id   string `json:"id"`
	Type string `json:"type"`
}

type announceActivityStruct struct {
	// TODO(#409): Change the object to simply be a createActivityObject
	// that's gathered by it's id in the original body.
	Actor     string                     `json:"actor"`
	Context   string                     `json:"@context"`
	Type      string                     `json:"type"`
	Published string                     `json:"published"`
	Object    createActivityObjectStruct `json:"object"`
	TargetID  string                     `json:"target"`
}

func (s *serverWrapper) handleAnnounceActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a announce activity.\n", recipient)

		decoder := json.NewDecoder(r.Body)
		var t announceActivityStruct
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		ats, err := parseTimestamp(w, t.Published, false)
		if err != nil {
			log.Printf("Unable to read announce timestamp: %v", err)
			return
		}

		ptc, err := parseTimestamp(w, t.Object.Published, true)
		if err != nil {
			log.Printf("Unable to read object timestamp: %v", err)
			return
		}

		f := &pb.ReceivedAnnounceDetails{
			AnnouncedObject: t.Object.Id,
			AnnouncerId:     t.Actor,
			AnnounceTime:    ats,
			Body:            t.Object.Content,
			AuthorApId:      t.Object.AttributedTo,
			Published:       ptc,
			Title:           t.Object.Name,
			TargetId:        t.TargetID,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.announce.ReceiveAnnounceActivity(ctx, f)
		if err != nil {
			log.Printf("Could not receive announce activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving announce activity.\n")
			return
		} else if resp.ResultType == pb.AnnounceResponse_ERROR {
			log.Printf("Could not receive announce activity. Error: %v",
				resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving announce activity.\n")
			return
		}

		log.Println("Announce activity received successfully.")
		fmt.Fprintf(w, "{}\n")
	}
}
