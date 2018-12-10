package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path"
	"strconv"
	"syscall"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/golang/protobuf/ptypes"
	tspb "github.com/golang/protobuf/ptypes/timestamp"
	"github.com/gorilla/mux"
	"github.com/gorilla/sessions"
	"google.golang.org/grpc"
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

// serverWrapper encapsulates the dependencies and config values of the server
// into one struct. Server endpoint handlers hang off of this struct and can
// access their dependencies through it. See
// https://medium.com/statuscode/how-i-write-go-http-services-after-seven-years-37c208122831
// for rationale and further explanation.
type serverWrapper struct {
	router *mux.Router
	server *http.Server
	store  *sessions.CookieStore

	// actorInboxRouter is responsible for routing activitypub requests
	// based on the Type json parameter
	actorInboxRouter map[string]http.HandlerFunc

	// shutdownWait specifies how long the server should wait when shutting
	// down for existing connections to finish before forcing a shutdown.
	shutdownWait time.Duration

	// databaseConn is the underlying connection to the Database
	// service. This reference must be retained so it can by closed later.
	databaseConn *grpc.ClientConn
	// database is the RPC client for talking to the database service.
	database pb.DatabaseClient

	followsConn               *grpc.ClientConn
	follows                   pb.FollowsClient
	articleConn               *grpc.ClientConn
	article                   pb.ArticleClient
	feedConn                  *grpc.ClientConn
	feed                      pb.FeedClient
	createConn                *grpc.ClientConn
	create                    pb.CreateClient
	usersConn                 *grpc.ClientConn
	users                     pb.UsersClient
	s2sFollowConn             *grpc.ClientConn
	s2sFollow                 pb.S2SFollowClient
	s2sLikeConn               *grpc.ClientConn
	s2sLike                   pb.S2SLikeClient
	approverConn              *grpc.ClientConn
	approver                  pb.ApproverClient
	rssConn                   *grpc.ClientConn
	rss                       pb.RSSClient
	followRecommendationsConn *grpc.ClientConn
	followRecommendations     pb.FollowRecommendationsClient
	ldNormConn                *grpc.ClientConn
	ldNorm                    pb.LDNormClient
	actorsConn                *grpc.ClientConn
	actors                    pb.ActorsClient
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

func (s *serverWrapper) handleFeed() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		v := mux.Vars(r)

		fr := &pb.FeedRequest{Username: v["username"]}
		resp, err := s.feed.Get(ctx, fr)
		if err != nil {
			log.Printf("Error in feed.Get(%v): %v\n", *fr, err)
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp.Results)
		if err != nil {
			log.Printf("could not marshal blogs: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
	}
}

func (s *serverWrapper) handleFeedPerUser() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		v := mux.Vars(r)
		if username, ok := v["username"]; !ok || username == "" {
			w.WriteHeader(http.StatusBadRequest) // Bad Request
			return
		}
		fr := &pb.FeedRequest{Username: v["username"]}
		resp, err := s.feed.PerUser(ctx, fr)
		if err != nil {
			log.Printf("Error in feed.PerUser(%v): %v", *fr, err)
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp.Results)
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
		resp, err := s.feed.PerArticle(ctx, fr)
		if err != nil {
			log.Printf("Error in getting per Article page: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)
		err = enc.Encode(resp.Results)
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
		// Even if the request was sent with a different follower user the
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
			log.Printf("Could not accept follow: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not accept follow.\n")
			return
		}

		if resp.ResultType != pb.FollowResponse_OK {
			log.Printf("Could not accept follow: %v", resp.Error)
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Could not accept follow.\n")
			return
		}

		w.Write([]byte("OK"))
	}
}

type likeStruct struct {
	ArticleId int64 `json:"article_id"`
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
			r.ErrorStr = "Issure with sending like"
			enc.Encode(r)
			return
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

func (s *serverWrapper) shutdown() {
	log.Printf("Stopping skinny server.\n")
	ctx, cancel := context.WithTimeout(context.Background(), s.shutdownWait)
	defer cancel()
	// Waits for active connections to terminate, or until it hits the timeout.
	s.server.Shutdown(ctx)

	s.databaseConn.Close()
	s.articleConn.Close()
	s.followsConn.Close()
	s.createConn.Close()
	s.feedConn.Close()
	s.usersConn.Close()
	s.s2sFollowConn.Close()
	s.rssConn.Close()
	s.actorsConn.Close()
}

func grpcConn(env string, port string) *grpc.ClientConn {
	host := os.Getenv(env)
	if host == "" {
		log.Fatalf("%s env var not set for skinny server.", env)
	}
	addr := host + ":" + port
	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect to %s: %v", addr, err)
	}
	return conn
}

func createArticleClient() (*grpc.ClientConn, pb.ArticleClient) {
	conn := grpcConn("ARTICLE_SERVICE_HOST", "1601")
	return conn, pb.NewArticleClient(conn)
}

func createCreateClient() (*grpc.ClientConn, pb.CreateClient) {
	conn := grpcConn("CREATE_SERVICE_HOST", "1922")
	return conn, pb.NewCreateClient(conn)
}

func createUsersClient() (*grpc.ClientConn, pb.UsersClient) {
	conn := grpcConn("USERS_SERVICE_HOST", "1534")
	return conn, pb.NewUsersClient(conn)
}

func createDatabaseClient() (*grpc.ClientConn, pb.DatabaseClient) {
	conn := grpcConn("DB_SERVICE_HOST", "1798")
	return conn, pb.NewDatabaseClient(conn)
}

func createFollowsClient() (*grpc.ClientConn, pb.FollowsClient) {
	conn := grpcConn("FOLLOWS_SERVICE_HOST", "1641")
	return conn, pb.NewFollowsClient(conn)
}

func createFeedClient() (*grpc.ClientConn, pb.FeedClient) {
	conn := grpcConn("FEED_SERVICE_HOST", "2012")
	return conn, pb.NewFeedClient(conn)
}

func createS2SFollowClient() (*grpc.ClientConn, pb.S2SFollowClient) {
	conn := grpcConn("FOLLOW_ACTIVITY_SERVICE_HOST", "1922")
	return conn, pb.NewS2SFollowClient(conn)
}

func createApproverClient() (*grpc.ClientConn, pb.ApproverClient) {
	conn := grpcConn("APPROVER_SERVICE_HOST", "2077")
	return conn, pb.NewApproverClient(conn)
}

func createS2SLikeClient() (*grpc.ClientConn, pb.S2SLikeClient) {
	conn := grpcConn("LIKE_SERVICE_HOST", "1848")
	return conn, pb.NewS2SLikeClient(conn)
}

func createRSSClient() (*grpc.ClientConn, pb.RSSClient) {
	conn := grpcConn("RSS_SERVICE_HOST", "1973")
	return conn, pb.NewRSSClient(conn)
}

func createFollowRecommendationsClient() (*grpc.ClientConn, pb.FollowRecommendationsClient) {
	conn := grpcConn("FOLLOW_RECOMMENDATIONS_HOST", "1973")
	return conn, pb.NewFollowRecommendationsClient(conn)
}

func createLDNormClient() (*grpc.ClientConn, pb.LDNormClient) {
	conn := grpcConn("LDNORM_SERVICE_HOST", "1804")
	return conn, pb.NewLDNormClient(conn)
}

func createActorsClient() (*grpc.ClientConn, pb.ActorsClient) {
	conn := grpcConn("ACTORS_SERVICE_HOST", "1973")
	return conn, pb.NewActorsClient(conn)
}

// buildServerWrapper sets up all necessary individual parts of the server
// wrapper, and returns one that is ready to run.
func buildServerWrapper() *serverWrapper {
	r := mux.NewRouter()
	env := "SKINNY_SERVER_PORT"
	port := os.Getenv(env)
	if port == "" {
		log.Fatalf("%s env var not set for skinny server", env)
	}
	addr := "0.0.0.0:" + port
	srv := &http.Server{
		Addr: addr,
		// Important to specify timeouts in order to prevent Slowloris attacks.
		WriteTimeout: time.Second * 15,
		ReadTimeout:  time.Second * 15,
		IdleTimeout:  time.Second * 60,
		Handler:      r,
	}
	cookie_store := sessions.NewCookieStore([]byte("rabble_key"))
	databaseConn, databaseClient := createDatabaseClient()
	followsConn, followsClient := createFollowsClient()
	articleConn, articleClient := createArticleClient()
	feedConn, feedClient := createFeedClient()
	createConn, createClient := createCreateClient()
	usersConn, usersClient := createUsersClient()
	rssConn, rssClient := createRSSClient()
	ldNormConn, ldNormClient := createLDNormClient()
	s2sFollowConn, s2sFollowClient := createS2SFollowClient()
	s2sLikeConn, s2sLikeClient := createS2SLikeClient()
	approverConn, approverClient := createApproverClient()
	followRecommendationsConn, followRecommendationsClient :=
		createFollowRecommendationsClient()
	actorsConn, actorsClient := createActorsClient()
	s := &serverWrapper{
		router:        r,
		server:        srv,
		store:         cookie_store,
		shutdownWait:  20 * time.Second,
		databaseConn:  databaseConn,
		database:      databaseClient,
		articleConn:   articleConn,
		article:       articleClient,
		followsConn:   followsConn,
		follows:       followsClient,
		feedConn:      feedConn,
		feed:          feedClient,
		createConn:    createConn,
		create:        createClient,
		usersConn:     usersConn,
		users:         usersClient,
		s2sFollowConn: s2sFollowConn,
		s2sFollow:     s2sFollowClient,
		s2sLikeConn:   s2sLikeConn,
		s2sLike:       s2sLikeClient,
		approver:      approverClient,
		approverConn:  approverConn,
		ldNorm:        ldNormClient,
		ldNormConn:    ldNormConn,
		rssConn:       rssConn,
		rss:           rssClient,
		followRecommendationsConn: followRecommendationsConn,
		followRecommendations:     followRecommendationsClient,
		actorsConn:                actorsConn,
		actors:                    actorsClient,
	}
	s.setupRoutes()
	return s
}

func main() {
	log.Printf("Starting skinny server.\n")
	s := buildServerWrapper()

	// The following code is partially taken from this link:
	// https://github.com/gorilla/mux#graceful-shutdown
	// It lays out a way for a server to gracefully shutdown when a SIGINT
	// (Ctrl+C) or SIGTERM (kill) is received.
	// See also: https://gobyexample.com/signals

	go func() {
		if err := s.server.ListenAndServe(); err != nil {
			log.Println(err)
		}
	}()

	// Accept graceful shutdowns when quit via SIGINT or SIGTERM. Other signals
	// (eg. SIGKILL, SIGQUIT) will not be caught.
	// Docker sends a SIGTERM on shutdown.
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)

	// Block until we receive signal.
	<-c
	s.shutdown()
	os.Exit(0)
}
