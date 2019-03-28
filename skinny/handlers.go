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
	"google.golang.org/grpc"
)

const (
	staticAssets         = "/repo/build_out/chump_dist"
	timeParseFormat      = "2006-01-02T15:04:05.000Z"
	protoTimeParseFormat = "2006-01-02T15:04:05.000000000Z"
	timeoutDuration      = time.Minute * 5
)

type clientResp struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

func parseTimestamp(w http.ResponseWriter, published string, old bool) (*tspb.Timestamp, error) {
	invalidCreationTimeMessage := "Invalid creation time\n"
	parseFormat := timeParseFormat
	if len(published) == 30 {
		parseFormat = protoTimeParseFormat
	}
	parsedCreationDatetime, timeErr := time.Parse(parseFormat, published)
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
		strUserID := v["userId"]
		userID := int64(0)
		if strUserID != "" {
			var err error
			userID, err = strconv.ParseInt(strUserID, 10, 64)
			if err != nil {
				log.Printf("Could not convert userId to int64: id(%v)\n", strUserID)
				w.WriteHeader(http.StatusBadRequest) // Bad Request.
				return
			}
		}

		fr := &pb.FeedRequest{UserId: userID}
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

		username, ok := v["username"]
		if !ok || username == "" {
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}

		fr := &pb.FeedRequest{Username: username}
		if global_id, err := s.getSessionGlobalId(r); err == nil {
			// If the user is logged in then propagate their global ID.
			fr.UserGlobalId = &wrapperpb.Int64Value{Value: global_id}
		}
		resp, err := s.feed.PerUser(ctx, fr)
		if err != nil {
			log.Printf("Error in feed.PerUser(%v): %v", *fr, err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		if resp.Error != pb.FeedResponse_NO_ERROR {
			w.WriteHeader(errorMap[resp.Error])
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
		strUserID, ok := v["userId"]
		if !ok || strUserID == "" {
			log.Printf("Could not parse userId from url in RssPerUserl\n")
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}
		userID, err := strconv.ParseInt(strUserID, 10, 64)
		if err != nil {
			log.Printf("Could not convert userId to int64: id(%v)\n", strUserID)
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}
		ue := &pb.UsersEntry{GlobalId: userID}
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

func (s *serverWrapper) handleUserCss() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		strUserID, ok := v["userId"]
		if !ok || strUserID == "" {
			log.Printf("Could not parse userId from url in UserCss\n")
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}
		userID, err := strconv.ParseInt(strUserID, 10, 64)
		if err != nil {
			log.Printf("Could not convert userId to int64: id(%v)\n", strUserID)
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		resp, err := s.users.GetCss(ctx, &pb.GetCssRequest{
			UserId: userID,
		})
		if err != nil {
			log.Printf("Error in users.GetCss: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		} else if resp.Result != pb.GetCssResponse_OK {
			log.Printf("Error getting css: %s", resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/css")
		fmt.Fprintf(w, resp.Css)
		return
	}
}

func (s *serverWrapper) handlePerArticlePage() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		log.Println("Per Article page called")

		v := mux.Vars(r)
		strArticleID, aOk := v["article_id"]
		if !aOk || strArticleID == "" {
			log.Println("Per Article page passed bad articleId value")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		articleID, string2IntErr := strconv.ParseInt(strArticleID, 10, 64)
		if string2IntErr != nil {
			log.Println("Article ID could not be converted to int")
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		fr := &pb.ArticleRequest{ArticleId: articleID}
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

type createArticleStruct struct {
	Author           string   `json:"author"`
	Body             string   `json:"body"`
	Title            string   `json:"title"`
	CreationDatetime string   `json:"creation_datetime"`
	Tags             []string `json:"tags"`
}

func (s *serverWrapper) handleCreateArticle() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var t createArticleStruct
		enc := json.NewEncoder(w)
		var cResp clientResp

		jsonErr := decoder.Decode(&t)
		if jsonErr != nil {
			log.Printf("Invalid JSON, Error: %s\n", jsonErr)
			w.WriteHeader(http.StatusBadRequest)
			cResp.Error = "Invalid JSON"
			enc.Encode(cResp)
			return
		}

		protoTimestamp, parseErr := parseTimestamp(w, t.CreationDatetime, false)
		if parseErr != nil {
			log.Println(parseErr)
			return
		}

		globalID, gIErr := s.getSessionGlobalId(r)
		if gIErr != nil {
			log.Printf("Create Article call from user not logged in")
			w.WriteHeader(http.StatusUnauthorized)
			cResp.Error = "Login Required"
			enc.Encode(cResp)
			return
		}

		na := &pb.NewArticle{
			AuthorId:         globalID,
			Body:             t.Body,
			Title:            t.Title,
			CreationDatetime: protoTimestamp,
			Foreign:          false,
			Tags:             t.Tags,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.article.CreateNewArticle(ctx, na)
		if err != nil {
			log.Printf("Could not create new article: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			cResp.Error = "Issue with creating article"
			enc.Encode(cResp)
			return
		}
		if resp.ResultType == pb.NewArticleResponse_ERROR {
			log.Printf("Could not create new article: %v", resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			cResp.Error = "Issue with creating article"
			enc.Encode(cResp)
			return
		}

		log.Printf("User Id: %#v attempted to create a post with title: %v\n", globalID, t.Title)
		w.WriteHeader(http.StatusOK)
		cResp.Message = "Article created"
		enc.Encode(cResp)
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

		protoTimestamp, parseErr := parseTimestamp(w, t.CreationDatetime, false)
		if parseErr != nil {
			log.Println(parseErr)
			return
		}

		globalID, gIErr := s.getSessionGlobalId(r)
		if gIErr != nil {
			log.Printf("Preview Article call from user not logged in")
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Login Required")
			return
		}

		na := &pb.NewArticle{
			AuthorId:         globalID,
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

		log.Printf("User Id: %#v attempted to create preview with title: %v\n", globalID, t.Title)
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
			// Send an unlike (undo)
			del := &pb.LikeUndoDetails{
				ArticleId:   t.ArticleId,
				LikerHandle: handle,
			}
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			resp, err := s.s2sUndo.SendLikeUndoActivity(ctx, del)
			if err != nil {
				log.Printf("Could not send undo: %v", err)
				w.WriteHeader(http.StatusInternalServerError)
				r.Success = false
				r.ErrorStr = "Issue with unliking"
				enc.Encode(r)
				return
			} else if resp.ResultType != pb.UndoResponse_OK {
				log.Printf("Could not send undo: %v", resp.Error)
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
		strUserID, ok := v["userId"]
		if !ok || strUserID == "" {
			log.Printf("Could not parse userId from url in handleRecommendFollows\n")
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}
		userID, err := strconv.ParseInt(strUserID, 10, 64)
		if err != nil {
			log.Printf("Could not convert userId to int64: id(%v)\n", strUserID)
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}

		req := &pb.FollowRecommendationRequest{UserId: userID}
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

func (s *serverWrapper) handleAddLog() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var v pb.ClientLog
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
		_, err = s.database.AddLog(ctx, &v)
		if err != nil {
			log.Printf("Could not add log: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
		}
	}
}

// handleAnnounce handles the parsing and sending an Announces.
//
// Note that only the Article ID is neccesary to send, both the
// Announcer ID and the timestamp get generated by this handler.
func (s *serverWrapper) handleAnnounce() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var v pb.AnnounceDetails
		err := decoder.Decode(&v)
		if err != nil {
			log.Printf("Invalid JSON. Err = %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		// We use their logged in GlobalID, since the client shouldn't
		// need to care about that detail.
		uid, err := s.getSessionGlobalId(r)
		if err != nil {
			log.Printf("Access denied in handleAnnounce: %v", err)
			w.WriteHeader(http.StatusForbidden)
			return
		}

		v.AnnouncerId = uid
		ts := ptypes.TimestampNow()
		v.AnnounceTime = ts

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		resp, err := s.announce.SendAnnounceActivity(ctx, &v)
		if err != nil {
			log.Printf("Could not send announce: %#v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		} else if resp.ResultType != pb.AnnounceResponse_OK {
			log.Printf("Could not send announce: %#v", resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusOK)
	}
}

type FollowGetter func(context.Context, *pb.GetFollowsRequest,
	...grpc.CallOption) (*pb.GetFollowsResponse, error)

func (s *serverWrapper) handleGetFollows(f FollowGetter) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		v := mux.Vars(r)
		username, ok := v["username"]
		if !ok || username == "" {
			w.WriteHeader(http.StatusBadRequest) // Bad Request.
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		fq := &pb.GetFollowsRequest{
			Username: username,
		}

		if uid, err := s.getSessionGlobalId(r); err == nil {
			fq.UserGlobalId = &wrapperpb.Int64Value{Value: uid}
		}

		followers, err := f(ctx, fq)
		if err != nil {
			log.Printf("Error in handleGetFollowers(): could not get followers: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(followers)
		if err != nil {
			log.Printf("could not marshal followers: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handleGetFollowers() http.HandlerFunc {
	return s.handleGetFollows(s.follows.GetFollowers)
}

func (s *serverWrapper) handleGetFollowing() http.HandlerFunc {
	return s.handleGetFollows(s.follows.GetFollowing)
}

func (s *serverWrapper) handlePostRecommendations() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		uid, err := s.getSessionGlobalId(r)
		if err != nil {
			log.Printf("Access denied in handlePostRecommendations: %v", err)
			w.WriteHeader(http.StatusForbidden)
			return
		}
		prr := &pb.PostRecommendationsRequest{UserId: uid}
		resp, err := s.postRecommendations.Get(ctx, prr)
		if err != nil {
			log.Printf("Error in postRecommendations.Get: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		if resp.ResultType != pb.PostRecommendationsResponse_OK {
			log.Printf("Error in postRecommendations.Get: %v", resp.Message)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp)
		if err != nil {
			log.Printf("Could not marshal post recommendations: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

// NoOpReplyStruct Reply structure for a noop request
type NoOpReplyStruct struct {
	Message string `json:"message"`
}

// handleNoOp is the handler for any service that is not running on this
// instance. The services that are configurable provide their docker routes as
// env vars to the skinny server. If those routes are equal to the no-op
// container skinny will route all calls to those services to this handler.
func (s *serverWrapper) handleNoOp() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		_, err := s.getSessionGlobalId(r)
		if err != nil {
			log.Printf("Access denied in handleNoOp: %v", err)
			w.WriteHeader(http.StatusForbidden)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)

		reply := NoOpReplyStruct{
			Message: "This option has been turned off on this rabble instance",
		}
		w.WriteHeader(http.StatusNotImplemented)
		enc.SetEscapeHTML(false)
		err = enc.Encode(reply)
		if err != nil {
			log.Printf("Could not marshal no op reply: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}
