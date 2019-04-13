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
	"strconv"
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

		log.Printf("Received activity to %#v's inbox: %#v\n", recipient, body)

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

// ImageObject holds the type of the image e.g. ".png" and the url
// where the image can be found
type ImageObject struct {
	Type string `json:"type"`
	URL  string `json:"url"`
}

// KeyObject holds information about the public key of a user such as the
// key id, the owner of the key and the publickey in string format
type KeyObject struct {
	ID           string `json:"id"`
	Owner        string `json:"owner"`
	PublicKeyPem string `json:"publicKeyPem"`
}

// ActorObjectStruct holds all fields that a ActivityPub actor should hold.
// see spec here: https://www.w3.org/TR/activitypub/#actor-objects
type ActorObjectStruct struct {
	// The @context in the output JSON-LD
	Context []string `json:"@context"`

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
	ID                string       `json:"id"`
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
			ID:                resp.Actor.Id,
		}

		actor.PublicKey = &KeyObject{
			ID:           resp.Actor.PublicKey.Id,
			Owner:        resp.Actor.PublicKey.Owner,
			PublicKeyPem: resp.Actor.PublicKey.PublicKeyPem,
		}

		filepath := s.getProfilePicPath(resp.Actor.GlobalId)
		if _, err := os.Stat(filepath); err == nil {
			// Profile pic exists
			actor.Icon = &ImageObject{
				Type: "Image",
				URL: fmt.Sprintf(
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
		fmt.Fprintf(w, resp.Collection)
		log.Printf("Created following collection successfully.")
	}
}

// ArticlePreviewStruct contatins details about the summary of the article
type ArticlePreviewStruct struct {
	Type    string `json:"type"`
	Content string `json:"content"`
	Name    string `json:"name"`
}

// ArticleContentStruct contains the article content and metadata
type ArticleContentStruct struct {
	// The @context in the output JSON-LD
	Context      []string              `json:"@context"`
	Type         string                `json:"type"`
	ID           string                `json:"id"`
	URL          string                `json:"url"`
	Content      string                `json:"content"`
	Name         string                `json:"name"`
	Published    string                `json:"published"`
	To           []string              `json:"to"`
	AttributedTo string                `json:"attributedTo"`
	Preview      *ArticlePreviewStruct `json:"preview"`
}

// ArticleObjectStruct contains activitypub formatted articles
type ArticleObjectStruct struct {
	// The @context in the output JSON-LD
	Context   []string              `json:"@context"`
	Type      string                `json:"type"`
	Actor     string                `json:"actor"`
	Object    *ArticleContentStruct `json:"object"`
	Published string                `json:"published"`
	ID        string                `json:"id"`
	To        []string              `json:"to"`
}

func (s *serverWrapper) handleAPArticle() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		u := v["username"]
		strArticleID, aOk := v["article_id"]
		if !aOk || strArticleID == "" {
			log.Println("Per Article AP passed bad articleId value")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		articleID, string2IntErr := strconv.ParseInt(strArticleID, 10, 64)
		if string2IntErr != nil {
			log.Println("ArticleAP ID could not be converted to int")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		req := &pb.ArticleApRequest{
			ArticleId: articleID,
			Username:  u,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.actors.GetArticle(ctx, req)
		if err != nil {
			log.Printf("Could not create article object. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create article object.\n")
			return
		}
		if resp.Actor == "" {
			log.Printf("Actors service GetArticle returned empty string\n")
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create article object.\n")
			return
		}

		context := []string{
			"https://www.w3.org/ns/activitystreams",
		}

		to := []string{
			"https://www.w3.org/ns/activitystreams#Public",
		}

		summaryContent := &ArticlePreviewStruct{
			Content: resp.Summary,
			Type:    "Note",
			Name:    "Summary",
		}

		articleContent := &ArticleContentStruct{
			Context:      context,
			Type:         "Create",
			ID:           resp.ApId,
			URL:          resp.ApId,
			Content:      resp.Content,
			Name:         resp.Title,
			Published:    resp.Published,
			To:           to,
			AttributedTo: resp.Actor,
			Preview:      summaryContent,
		}

		article := &ArticleObjectStruct{
			Context:   context,
			Type:      "Create",
			Actor:     resp.Actor,
			To:        to,
			ID:        resp.ApId,
			Published: resp.Published,
			Object:    articleContent,
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		err = enc.Encode(article)
		if err != nil {
			log.Printf("Could not marshal Article object. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not create article object.\n")
			return
		}
		log.Printf("Created article successfully.")
	}
}

type articleObjectStruct struct {
	Content      string               `json:"content"`
	Name         string               `json:"name"`
	Published    string               `json:"published"`
	AttributedTo string               `json:"attributedTo"`
	Type         string               `json:"type"`
	ID           string               `json:"id"`
	URL          string               `json:"url"`
	Preview      articleObjectPreview `json:"preview"`
}

type articleObjectPreview struct {
	Type    string `json:"type"`
	Name    string `json:"name"`
	Content string `json:"content"`
}

type createActivityStruct struct {
	Actor     string              `json:"actor"`
	Object    articleObjectStruct `json:"object"`
	Recipient []string            `json:"to"`
	Type      string              `json:"type"`
}

func (s *serverWrapper) handleCreateActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		var cResp clientResp

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

		protoTimestamp, parseErr := parseTimestamp(w, t.Object.Published, &cResp)
		if parseErr != nil {
			log.Println(parseErr)
			enc.Encode(cResp)
			return
		}

		summary := ""
		if t.Object.Preview.Type == "Note" && t.Object.Preview.Name == "Summary" {
			summary = t.Object.Preview.Content
		}

		if bad := s.blacklist.Actors(w, t.Actor, t.Object.AttributedTo); bad {
			return
		}

		nfa := &pb.NewForeignArticle{
			AttributedTo: t.Object.AttributedTo,
			Content:      t.Object.Content,
			Published:    protoTimestamp,
			Recipient:    recipient,
			Title:        t.Object.Name,
			Id:           t.Object.ID,
			Summary:      summary,
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

type updateActivity struct {
	Object articleObjectStruct `json:"object"`
	Type   string              `json:"type"`
}

func (s *serverWrapper) handleUpdateActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received an update activity\n", recipient)

		decoder := json.NewDecoder(r.Body)
		var t updateActivity
		err := decoder.Decode(&t)
		if err != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", err)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		summary := ""
		if t.Object.Preview.Type == "Note" && t.Object.Preview.Name == "Summary" {
			summary = t.Object.Preview.Content
		}

		if bad := s.blacklist.Actors(w, t.Object.AttributedTo); bad {
			return
		}

		ud := &pb.ReceivedUpdateDetails{
			ApId:    t.Object.ID,
			Body:    t.Object.Content,
			Title:   t.Object.Name,
			Summary: summary,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sUpdate.ReceiveUpdateActivity(ctx, ud)
		if err != nil || resp.ResultType == pb.UpdateResponse_ERROR {
			if err != nil {
				log.Printf("Could not receive update activity. Error: %v", err)
			} else {
				log.Printf("Could not receive update activity. Error: %v", resp.Error)
			}
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving update activity\n")
			return
		}

		log.Printf("Update activity was successfully processed\n")
		fmt.Fprintf(w, "Update successful\n")
	}
}

type followActivityStruct struct {
	Actor     string   `json:"actor"`
	Object    string   `json:"object"`
	Recipient []string `json:"to"`
	Type      string   `json:"type"`
}

func (s *serverWrapper) handleFollowActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		if recipient, ok := v["username"]; ok {
			log.Printf("User %v received a follow activity.\n", recipient)
		}

		// TODO: Parse JSON-LD in other shapes.
		decoder := json.NewDecoder(r.Body)
		var t followActivityStruct
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\nError: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		if bad := s.blacklist.Actors(w, t.Actor); bad {
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
			return
		}

		log.Println("Activity received successfully.")
	}
}

type followUndoActivity struct {
	Object followActivityStruct `json:"object"`
	Type   string               `json:"type"`
}

func (s *serverWrapper) handleFollowUndoActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var t followUndoActivity

		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		f := &pb.ReceivedFollowDetails{
			Follower: t.Object.Actor,
			Followed: t.Object.Object,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sFollow.ReceiveUnfollowActivity(ctx, f)
		if err != nil || resp.ResultType == pb.FollowActivityResponse_ERROR {
			log.Printf("Could not receive undo follow activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving undo follow activity.\n")
			return
		}

		log.Println("Activity received successfully.")
	}
}

type likeActorStruct struct {
	ID   string `json:"id"`
	Type string `json:"type"`
}

type likeActivityStruct struct {
	Actor  likeActorStruct `json:"actor"`
	Object string          `json:"object"`
	Type   string          `json:"type"`
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

		if bad := s.blacklist.Actors(w, t.Actor.ID); bad {
			return
		}

		f := &pb.ReceivedLikeDetails{
			LikedObject: t.Object,
			LikerId:     t.Actor.ID,
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

type deleteActivity struct {
	Object string `json:"object"`
	Actor  string `json:"actor"`
}

func (s *serverWrapper) handleDeleteActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a delete activity.\n", recipient)

		// TODO(iandioch, sailslick, CianLR, devoxel): Parse JSON-LD in other shapes.
		decoder := json.NewDecoder(r.Body)
		var t deleteActivity
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		if bad := s.blacklist.Actors(w, t.Actor); bad {
			return
		}

		f := &pb.ReceivedDeleteDetails{
			ApId: t.Object,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sDelete.ReceiveDeleteActivity(ctx, f)
		if err != nil {
			log.Printf("Could not receive delete activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving delete activity.\n")
			return
		} else if resp.ResultType == pb.DeleteResponse_ERROR {
			log.Printf("Could not receive delete activity. Error: %v",
				resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving delete activity.\n")
			return
		} else if resp.ResultType == pb.DeleteResponse_DENIED {
			log.Printf("Delete activity is denied")
			w.WriteHeader(http.StatusUnauthorized)
			fmt.Fprintf(w, "Delete activity is denied")
			return
		}

		log.Println("Delete activity received successfully.")
		fmt.Fprintf(w, "Delete activity received successfully.")
	}
}

type approvalObject struct {
	Actor  string `json:"actor"`
	Object string `json:"object"`
	Type   string `json:"type"`
}

type approvalActivity struct {
	Actor     string         `json:"actor"`
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

		if bad := s.blacklist.Actors(w, t.Actor, t.Object.Object); bad {
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

type undoActivity struct {
	Object activity `json:"object"`
	Type   string   `json:"type"`
}

func (s *serverWrapper) handleUndoActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a undo activity.\n", recipient)

		// Pass control to corresponding undo type
		buf := new(bytes.Buffer)
		buf.ReadFrom(r.Body)
		body := buf.String()

		d := json.NewDecoder(strings.NewReader(body))
		var del undoActivity

		if err := d.Decode(&del); err != nil {
			log.Printf("Could not decode Undo activity: %#v", err)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Could not decode Undo activity")
			return
		}

		if s.undoActivityRouter == nil || len(s.undoActivityRouter) == 0 {
			log.Fatalf("Undo router not initalized, can not continue.")
		}

		// Similarily to the actorInboxRouter different functions are called
		// depending on the type of the object to be undone.
		m, exists := s.undoActivityRouter[strings.ToLower(del.Object.Type)]
		if !exists {
			log.Printf("Could not find undo handle for object of type %#v",
				del.Object.Type)
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintf(w, "Could not handle Undo activity for '%#v'",
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

type likeUndoActivity struct {
	Object likeActivityStruct `json:"object"`
	Type   string             `json:"type"`
}

func (s *serverWrapper) handleLikeUndoActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received a like Undo activity.\n", recipient)

		decoder := json.NewDecoder(r.Body)
		var t likeUndoActivity

		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		if bad := s.blacklist.Actors(w, t.Object.Actor.ID); bad {
			return
		}
		f := &pb.ReceivedLikeUndoDetails{
			LikedObjectApId: t.Object.Object,
			LikingUserApId:  t.Object.Actor.ID,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.s2sUndo.ReceiveLikeUndoActivity(ctx, f)
		if err != nil {
			log.Printf("Could not receive like undo activity. Error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving like undo activity.\n")
			return
		} else if resp.ResultType == pb.UndoResponse_ERROR {
			log.Printf("Could not receive like undo activity. Error: %v",
				resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with receiving like undo activity.\n")
			return
		}

		log.Println("Like undo activity received successfully.")
		fmt.Fprintf(w, "{}\n")
	}
}

// TODO(sailslick): Properly fill in announce structs
type announceActor struct {
	ID   string `json:"id"`
	Type string `json:"type"`
}

type announceActivityStruct struct {
	// TODO(#409): Change the object to simply be a createActivityObject
	// that's gathered by its id in the original body.
	Actor     string              `json:"actor"`
	Type      string              `json:"type"`
	Published string              `json:"published"`
	Object    articleObjectStruct `json:"object"`
	TargetID  string              `json:"target"`
}

func (s *serverWrapper) handleAnnounceActivity() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		recipient := v["username"]
		log.Printf("User %v received an announce activity.\n", recipient)
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		var cResp clientResp

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

		ats, err := parseTimestamp(w, t.Published, &cResp)
		if err != nil {
			log.Printf("Unable to read announce timestamp: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			enc.Encode(cResp)
			return
		}

		ptc, err := parseTimestamp(w, t.Object.Published, &cResp)
		if err != nil {
			log.Printf("Unable to read object timestamp: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			enc.Encode(cResp)
			return
		}

		if bad := s.blacklist.Actors(w, t.Actor, t.Object.AttributedTo); bad {
			return
		}

		f := &pb.ReceivedAnnounceDetails{
			AnnouncedObject: t.Object.ID,
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
