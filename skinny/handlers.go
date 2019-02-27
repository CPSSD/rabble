package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"path"
	"strconv"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	util "github.com/cpssd/rabble/services/utils"
	"github.com/golang/protobuf/ptypes"
	tspb "github.com/golang/protobuf/ptypes/timestamp"
	wrapperpb "github.com/golang/protobuf/ptypes/wrappers"
	"github.com/gorilla/mux"
)

const (
	staticAssets    = "/repo/build_out/chump_dist"
	timeParseFormat = "2006-01-02T15:04:05.000Z"
	timeoutDuration = time.Minute * 5
)

type createArticleStruct struct {
	Author           string `json:"author"`
	Body             string `json:"body"`
	Title            string `json:"title"`
	CreationDatetime string `json:"creation_datetime"`
}

func parseTimestamp(w http.ResponseWriter, published string) (*tspb.Timestamp, error) {
	invalidCreationTimeMessage := "Invalid creation time\n"

	parsedCreationDatetime, timeErr := time.Parse(timeParseFormat, published)
	if timeErr != nil {
		log.Printf("Error: %s\n", timeErr)
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, invalidCreationTimeMessage)
		return nil, fmt.Errorf(invalidCreationTimeMessage)
	}

	protoTimestamp, protoTimeErr := ptypes.TimestampProto(parsedCreationDatetime)
	if protoTimeErr != nil {
		log.Printf("Error: %s\n", protoTimeErr)
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, invalidCreationTimeMessage)
		return nil, fmt.Errorf(invalidCreationTimeMessage)
	}

	timeSinceRequest := time.Since(parsedCreationDatetime)
	if timeSinceRequest >= timeoutDuration || timeSinceRequest < 0 {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, "Old creation time\n")
		return nil, fmt.Errorf("Old creation time")
	}
	return protoTimestamp, nil
}

func (s *serverWrapper) getSessionHandle(r *http.Request) (string, error) {
	session, err := s.store.Get(r, "rabble-session")
	if err != nil {
		log.Printf("Error getting session: %v", err)
		return "", err
	}
	if _, ok := session.Values["handle"]; !ok {
		return "", fmt.Errorf("Handle doesn't exist, user not logged in")
	}
	return session.Values["handle"].(string), nil
}

func (s *serverWrapper) getSessionGlobalId(r *http.Request) (int64, error) {
	session, err := s.store.Get(r, "rabble-session")
	if err != nil {
		log.Printf("Error getting session: %v", err)
		return 0, err
	}
	if _, ok := session.Values["global_id"]; !ok {
		return 0, fmt.Errorf("Global ID doesn't exist, user not logged in")
	}
	return session.Values["global_id"].(int64), nil
}

func (s *serverWrapper) handleFeed() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		v := mux.Vars(r)

		fr := &pb.FeedRequest{Username: v["username"]}
		if global_id, err := s.getSessionGlobalId(r); err == nil {
			// If the user is logged in then propagate their global ID.
			fr.UserGlobalId = &wrapperpb.Int64Value{Value: global_id}
		}
		resp, err := s.feed.Get(ctx, fr)
		if err != nil {
			log.Printf("Error in feed.Get(%v): %v\n", *fr, err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp)
		if err != nil {
			log.Printf("could not marshal blogs: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handleFeedPerUser() http.HandlerFunc {
	errorMap := map[pb.FeedResponse_FeedError]int{
		pb.FeedResponse_USER_NOT_FOUND: 404,
		pb.FeedResponse_UNAUTHORIZED:   401,
	}
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		v := mux.Vars(r)
		if username, ok := v["username"]; !ok || username == "" {
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}

		fr := &pb.FeedRequest{Username: v["username"]}
		if global_id, err := s.getSessionGlobalId(r); err == nil {
			// If the user is logged in then propagate their global ID.
			fr.UserGlobalId = &wrapperpb.Int64Value{Value: global_id}
		}
		resp, err := s.feed.PerUser(ctx, fr)
		if resp.Error != pb.FeedResponse_NO_ERROR {
			w.WriteHeader(errorMap[resp.Error])
			return
		}

		if err != nil {
			log.Printf("Error in feed.PerUser(%v): %v", *fr, err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp)
		if err != nil {
			log.Printf("could not marshal blogs: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handleRssPerUser() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		v := mux.Vars(r)
		if username, ok := v["username"]; !ok || username == "" {
			w.WriteHeader(http.StatusBadRequest) // Bad Request
			return
		}
		ue := &pb.UsersEntry{Handle: v["username"]}
		resp, err := s.rss.PerUserRss(ctx, ue)
		if err != nil {
			log.Printf("Error in rss.PerUserRss(%v): %v", *ue, err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		if resp.ResultType == pb.RssResponse_ERROR {
			log.Printf("Error in rss.PerUserRss(%v): %v", *ue, resp.Message)
			w.WriteHeader(http.StatusBadRequest)
			return
		}
		if resp.ResultType == pb.RssResponse_DENIED {
			log.Printf("Access denied in rss.PerUserRss(%v): %v", *ue, resp.Message)
			w.WriteHeader(http.StatusForbidden)
			return
		}

		w.Header().Set("Content-Type", "application/rss+xml")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, resp.Feed)
	}
}

func (s *serverWrapper) handlePerArticlePage() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		log.Println("Per Article page called")

		v := mux.Vars(r)
		username, uOk := v["username"]
		strArticleId, aOk := v["article_id"]
		if !uOk || !aOk || strArticleId == "" || username == "" {
			log.Println("Per Article page passed bad url values")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		articleId, string2IntErr := strconv.ParseInt(strArticleId, 10, 64)

		if string2IntErr != nil {
			log.Println("Article ID could not be converted to int")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		fr := &pb.ArticleRequest{ArticleId: articleId}
		if global_id, err := s.getSessionGlobalId(r); err == nil {
			// If the user is logged in then propagate their global ID.
			fr.UserGlobalId = &wrapperpb.Int64Value{Value: global_id}
		}
		resp, err := s.feed.PerArticle(ctx, fr)
		if err != nil {
			log.Printf("Error in getting per Article page: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp)
		if err != nil {
			log.Printf("Could not marshal article: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

// handleNotImplemented returns a http.HandlerFunc with a 501 Not Implemented
// error.
func (s *serverWrapper) handleNotImplemented() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		http.Error(
			w,
			http.StatusText(http.StatusNotImplemented),
			http.StatusNotImplemented)
	}
}

func (s *serverWrapper) getIndexFile() []byte {
	// This flag is used in "go test", so we can use that to check if we're
	// in a test.
	if flag.Lookup("test.v") != nil {
		return []byte("testing html")
	}

	indexPath := path.Join(staticAssets, "index.html")
	b, err := ioutil.ReadFile(indexPath)
	if err != nil {
		log.Fatalf("could not find index.html: %v", err)
	}
	return b
}

func (s *serverWrapper) handleIndex() http.HandlerFunc {
	b := s.getIndexFile()
	return func(w http.ResponseWriter, r *http.Request) {
		_, err := w.Write(b)
		if err != nil {
			log.Printf("handleIndex failed to write: %v\n", err)
		}
	}
}

func (s *serverWrapper) handleFollow() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var j pb.LocalToAnyFollow
		err := decoder.Decode(&j)
		enc := json.NewEncoder(w)
		if err != nil {
			log.Printf("Invalid JSON. Err = %#v", err)
			w.WriteHeader(http.StatusBadRequest)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
			return
		}

		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Call to follow by not logged in user")
			w.WriteHeader(http.StatusBadRequest)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Login required",
			}
			enc.Encode(e)
			return
		}
		// Even if the request was sent with a different follower, use the
		// handle of the logged in user.
		j.Follower = handle

		ts := ptypes.TimestampNow()
		j.Datetime = ts

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		resp, err := s.follows.SendFollowRequest(ctx, &j)
		if err != nil {
			log.Printf("Could not send follow request: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
			return
		}

		err = enc.Encode(resp)
		if err != nil {
			log.Printf("Could not marshal follow result: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
		}
	}
}

func (s *serverWrapper) handleUnfollow() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var j pb.LocalToAnyFollow
		err := decoder.Decode(&j)
		enc := json.NewEncoder(w)
		if err != nil {
			log.Printf("Invalid JSON. Err = %#v", err)
			w.WriteHeader(http.StatusBadRequest)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
			return
		}

		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Call to unfollow by not logged in user")
			w.WriteHeader(http.StatusBadRequest)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Login required",
			}
			enc.Encode(e)
			return
		}
		// Even if the request was sent with a different follower, use the
		// handle of the logged in user.
		j.Follower = handle

		ts := ptypes.TimestampNow()
		j.Datetime = ts

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		resp, err := s.follows.SendUnfollow(ctx, &j)
		if err != nil {
			log.Printf("Could not send unfollow: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
			return
		}

		err = enc.Encode(resp)
		if err != nil {
			log.Printf("Could not marshal unfollow result: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
		}
	}
}

func (s *serverWrapper) handleRssFollow() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var j pb.LocalToRss
		err := decoder.Decode(&j)
		enc := json.NewEncoder(w)
		if err != nil {
			log.Printf("Invalid JSON. Err = %#v", err)
			w.WriteHeader(http.StatusBadRequest)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
			return
		}

		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Call to follow rss by not logged in user")
			w.WriteHeader(http.StatusBadRequest)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Login required",
			}
			enc.Encode(e)
			return
		}

		// Even if the request was sent with a different follower user the
		// handle of the logged in user.
		j.Follower = handle

		ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
		defer cancel()
		resp, err := s.follows.RssFollowRequest(ctx, &j)
		if err != nil {
			log.Printf("Could not send rss follow request: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
			return
		}

		err = enc.Encode(resp)
		if err != nil {
			log.Printf("Could not marshal rss follow result: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			e := &pb.FollowResponse{
				ResultType: pb.FollowResponse_ERROR,
				Error:      "Invalid JSON",
			}
			enc.Encode(e)
		}
	}
}

func (s *serverWrapper) handleCreateArticle() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var t createArticleStruct
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		protoTimestamp, parseErr := parseTimestamp(w, t.CreationDatetime)
		if parseErr != nil {
			log.Println(parseErr)
			return
		}

		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Create Article call from user not logged in")
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Login Required")
			return
		}

		na := &pb.NewArticle{
			Author:           handle,
			Body:             t.Body,
			Title:            t.Title,
			CreationDatetime: protoTimestamp,
			Foreign:          false,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.article.CreateNewArticle(ctx, na)
		if err != nil {
			log.Printf("Could not create new article: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with creating article\n")
			return
		}

		log.Printf("User %#v attempted to create a post with title: %v\n", t.Author, t.Title)
		fmt.Fprintf(w, "Created blog with title: %v and result type: %d\n", t.Title, resp.ResultType)
		// TODO(sailslick) send the response
	}
}

func (s *serverWrapper) handlePreviewArticle() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var t createArticleStruct
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON\n")
			return
		}

		protoTimestamp, parseErr := parseTimestamp(w, t.CreationDatetime)
		if parseErr != nil {
			log.Println(parseErr)
			return
		}

		na := &pb.NewArticle{
			Author:           t.Author,
			Body:             t.Body,
			Title:            t.Title,
			CreationDatetime: protoTimestamp,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.article.PreviewArticle(ctx, na)
		if err != nil {
			log.Printf("Could not create preview. Err: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with creating preview\n")
			return
		}

		log.Printf("User %#v attempted to create preview with title: %v\n", t.Author, t.Title)
		w.Header().Set("Content-Type", "application/json")
		// TODO(devoxel): Remove SetEscapeHTML and properly handle that client side
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp.Preview)
		if err != nil {
			log.Printf("could not marshal post: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handlePendingFollows() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {

		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Call to follow by not logged in user")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		pr := &pb.PendingFollowRequest{
			Handle: handle,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.database.PendingFollows(ctx, pr)
		if err != nil {
			log.Printf("Could not get pending follows. Err: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with finding pending follows.\n")
			return
		}

		if resp.ResultType != pb.PendingFollowResponse_OK {
			log.Printf("Could not get pending follows. Err: %v", resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Issue with finding pending follows.\n")
			return
		}

		log.Print(resp)
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		err = enc.Encode(resp)
		if err != nil {
			log.Printf("could not marshal pending response: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handleAcceptFollow() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		_, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Call to follow by not logged in user")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		decoder := json.NewDecoder(r.Body)
		var af pb.AcceptFollowRequest
		err = decoder.Decode(&af)
		if err != nil {
			log.Printf("Invalid JSON: %#v", err)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid JSON.\n")
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		resp, err := s.follows.AcceptFollow(ctx, &af)
		if err != nil {
			log.Printf("Could not modify follow: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not modify follow.\n")
			return
		}

		if resp.ResultType != pb.FollowResponse_OK {
			log.Printf("Could not modify follow: %v", resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not modify follow.\n")
			return
		}

		w.Write([]byte("OK"))
	}
}

type likeStruct struct {
	ArticleId int64 `json:"article_id"`
	IsLiked   bool  `json:"is_liked"`
}

type likeResponse struct {
	Success  bool   `json:"success"`
	ErrorStr string `json:"error_str"`
}

func (s *serverWrapper) handleLike() http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		decoder := json.NewDecoder(req.Body)
		var t likeStruct
		var r likeResponse
		enc := json.NewEncoder(w)
		w.Header().Set("Content-Type", "application/json")
		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON\n")
			log.Printf("Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			r.Success = false
			r.ErrorStr = jsonErr.Error()
			enc.Encode(r)
			return
		}

		handle, err := s.getSessionHandle(req)
		if err != nil {
			log.Printf("Like call from user not logged in")
			w.WriteHeader(http.StatusBadRequest)
			r.Success = false
			r.ErrorStr = "Login Required"
			enc.Encode(r)
			return
		}

		if t.IsLiked {
			// Send a like
			like := &pb.LikeDetails{
				ArticleId:   t.ArticleId,
				LikerHandle: handle,
			}
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			resp, err := s.s2sLike.SendLikeActivity(ctx, like)
			if err != nil {
				log.Printf("Could not send like: %v", err)
				w.WriteHeader(http.StatusInternalServerError)
				r.Success = false
				r.ErrorStr = "Issue with sending like"
				enc.Encode(r)
				return
			} else if resp.ResultType != pb.LikeResponse_OK {
				log.Printf("Could not send like: %v", resp.Error)
				w.WriteHeader(http.StatusInternalServerError)
				r.Success = false
				r.ErrorStr = "Issue with sending like"
				enc.Encode(r)
				return
			}
		} else {
			// Send an unlike (delete)
			del := &pb.LikeDeleteDetails{
				ArticleId: t.ArticleId,
				LikerHandle: handle,
			}
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			resp, err := s.s2sDelete.SendLikeDeleteActivity(ctx, del)
			if err != nil {
				log.Printf("Could not send delete: %v", err)
				w.WriteHeader(http.StatusInternalServerError)
				r.Success = false
				r.ErrorStr = "Issue with unliking"
				enc.Encode(r)
				return
			} else if resp.ResultType != pb.DeleteResponse_OK {
				log.Printf("Could not send delete: %v", resp.Error)
				w.WriteHeader(http.StatusInternalServerError)
				r.Success = false
				r.ErrorStr = "Issue with unliking"
				enc.Encode(r)
				return
			}
		}
		r.Success = true
		enc.Encode(r)
	}
}

func (s *serverWrapper) handleRecommendFollows() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		v := mux.Vars(r)
		if username, ok := v["username"]; !ok || username == "" {
			w.WriteHeader(http.StatusBadRequest) // Bad Request
			return
		}

		req := &pb.FollowRecommendationRequest{Username: v["username"]}
		resp, err := s.followRecommendations.GetFollowRecommendations(ctx, req)
		if err != nil {
			log.Printf("Error in handleRecommendFollows(%v): %v", *req, err)
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp.Results)
		if err != nil {
			log.Printf("Could not marshal recommended follows: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

type SearchResult struct {
	Posts []*pb.Post `json:"posts"`
	Users []*pb.User `json:"users"`
}

func (s *serverWrapper) handleSearch() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		query := r.URL.Query().Get("query")
		if query == "" {
			w.WriteHeader(http.StatusBadRequest) // Bad Request
			return
		}
		query, qUErr := url.QueryUnescape(query)
		if qUErr != nil {
			log.Printf("Error in Search(%v) query unescape: %v", query, qUErr)
			w.WriteHeader(http.StatusBadRequest) // Bad Request
			return
		}

		sq := &pb.SearchQuery{QueryText: query}
		req := &pb.SearchRequest{Query: sq}
		if global_id, gIErr := s.getSessionGlobalId(r); gIErr == nil {
			// If the user is logged in then propagate their global ID.
			req.UserGlobalId = &wrapperpb.Int64Value{Value: global_id}
		}
		resp, err := s.search.Search(ctx, req)
		if err != nil {
			log.Printf("Error in Search(%v): %v", *req, err)
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		body := &SearchResult{Users: resp.UResults, Posts: resp.Results}
		err = enc.Encode(body)
		if err != nil {
			log.Printf("Could not marshal recommended follows: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handleUserDetails() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		handle, err := s.getSessionHandle(r)
		if err != nil {
			log.Printf("Called user details without logging in: %v", err)
			w.WriteHeader(http.StatusForbidden)
			return
		}

		ur := &pb.UsersRequest{
			RequestType: pb.UsersRequest_FIND,
			Match: &pb.UsersEntry{
				Handle:     handle,
				HostIsNull: true,
			},
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		resp, err := s.database.Users(ctx, ur)
		if err != nil {
			log.Printf("could not get user, error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		} else if len(resp.Results) != 1 {
			log.Printf("could not get user, got %v results", len(resp.Results))
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(util.StripUser(resp.Results[0]))
		if err != nil {
			log.Printf("could not marshal blogs: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handleTrackView() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var v pb.View
		err := decoder.Decode(&v)
		if err != nil {
			log.Printf("Invalid JSON. Err = %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		// uid = 0 if no user is logged in.
		uid, err := s.getSessionGlobalId(r)

		v.User = uid

		ts := ptypes.TimestampNow()
		v.Datetime = ts

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		_, err = s.database.AddView(ctx, &v)
		if err != nil {
			log.Printf("Could not send view: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
		}
	}
}
