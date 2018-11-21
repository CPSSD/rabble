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

type createArticleStruct struct {
	Author           string `json:"author"`
	Body             string `json:"body"`
	Title            string `json:"title"`
	CreationDatetime string `json:"creation_datetime"`
}

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

type registerResponse struct {
	Error   string `json:"error"`
	Success bool   `json:"success"`
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
	// shutdownWait specifies how long the server should wait when shutting
	// down for existing connections to finish before forcing a shutdown.
	shutdownWait time.Duration

	// databaseConn is the underlying connection to the Database
	// service. This reference must be retained so it can by closed later.
	databaseConn *grpc.ClientConn
	// database is the RPC client for talking to the database service.
	database pb.DatabaseClient

	followsConn   *grpc.ClientConn
	follows       pb.FollowsClient
	articleConn   *grpc.ClientConn
	article       pb.ArticleClient
	feedConn      *grpc.ClientConn
	feed          pb.FeedClient
	createConn    *grpc.ClientConn
	create        pb.CreateClient
	usersConn     *grpc.ClientConn
	users         pb.UsersClient
	s2sFollowConn *grpc.ClientConn
	s2sFollow     pb.S2SFollowClient
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
		// TODO(devoxel): Remove SetEscapeHTML and properly handle that client side
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
			log.Print("Error in feed.PerUser(%v): %v", *fr, err)
		}

		w.Header().Set("Content-Type", "application/json")
		// TODO(devoxel): Remove SetEscapeHTML and properly handle that client side
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

func (s *serverWrapper) handlePerArticlePage() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

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
			log.Print("Error in getting per Article page: %v", err)
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
			log.Fatalf("Could not send follow request: %#v", err)
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

// handleRegister sends an RPC to the users service to create a user with the
// given info.
func (s *serverWrapper) handleRegister() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		decoder := json.NewDecoder(r.Body)
		var req registerRequest
		var jsonResp registerResponse
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

// setupRoutes specifies the routing of all endpoints on the server.
// Centralised routing config allows easier debugging of a specific endpoint,
// as the code handling it can be looked up here.
// The server uses mux for routing. See instructions and examples for mux at
// https://www.gorillatoolkit.org/pkg/mux .
// TODO(iandioch): Move setupRoutes() to its own file if/when it gets too big.
func (s *serverWrapper) setupRoutes() {
	const (
		assetPath = "/assets/"
	)
	log.Printf("Setting up routes on skinny server.\n")

	r := s.router
	fs := http.StripPrefix(assetPath, http.FileServer(http.Dir(staticAssets)))

	r.PathPrefix(assetPath).Handler(fs)

	// User-facing routes
	r.HandleFunc("/", s.handleIndex())

	// c2s routes
	r.HandleFunc("/c2s/create_article", s.handleCreateArticle())
	r.HandleFunc("/c2s/preview_article", s.handlePreviewArticle())
	r.HandleFunc("/c2s/feed", s.handleFeed())
	r.HandleFunc("/c2s/feed/{username}", s.handleFeed())
	r.HandleFunc("/c2s/@{username}", s.handleFeedPerUser())
	r.HandleFunc("/c2s/@{username}/{article_id}", s.handlePerArticlePage())
	r.HandleFunc("/c2s/follow", s.handleFollow())
	r.HandleFunc("/c2s/register", s.handleRegister())
	r.HandleFunc("/c2s/login", s.handleLogin())
	r.HandleFunc("/c2s/logout", s.handleLogout())

	// ActivityPub routes
	r.HandleFunc("/ap/", s.handleNotImplemented())
	r.HandleFunc("/ap/@{username}/inbox", s.handleCreateActivity())
	r.HandleFunc("/ap/@{username}/inbox_follow", s.handleFollowActivity())
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
}

func createArticleClient() (*grpc.ClientConn, pb.ArticleClient) {
	host := os.Getenv("ARTICLE_SERVICE_HOST")
	if host == "" {
		log.Fatal("ARTICLE_SERVICE_HOST env var not set for skinny server.")
	}
	addr := host + ":1601"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect to Article: %v", err)
	}
	return conn, pb.NewArticleClient(conn)
}

func createCreateClient() (*grpc.ClientConn, pb.CreateClient) {
	host := os.Getenv("CREATE_SERVICE_HOST")
	if host == "" {
		log.Fatal("CREATE_SERVICE_HOST env var not set for skinny server.")
	}
	addr := host + ":1922"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect to Create: %v", err)
	}
	return conn, pb.NewCreateClient(conn)
}

func createUsersClient() (*grpc.ClientConn, pb.UsersClient) {
	host := os.Getenv("USERS_SERVICE_HOST")
	if host == "" {
		log.Fatal("USERS_SERVICE_HOST env var not set for skinny server.")
	}
	addr := host + ":1534"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect to Users: %v", err)
	}
	return conn, pb.NewUsersClient(conn)
}

func createDatabaseClient() (*grpc.ClientConn, pb.DatabaseClient) {
	host := os.Getenv("DB_SERVICE_HOST")
	if host == "" {
		log.Fatal("DB_SERVICE_HOST env var not set for skinny server.")
	}
	addr := host + ":1798"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect: %v", err)
	}
	client := pb.NewDatabaseClient(conn)
	return conn, client
}

func createFollowsClient() (*grpc.ClientConn, pb.FollowsClient) {
	host := os.Getenv("FOLLOWS_SERVICE_HOST")
	if host == "" {
		log.Fatal("FOLLOWS_SERVICE_HOST env var not set for skinny server.")
	}
	addr := host + ":1641"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect: %v", err)
	}
	client := pb.NewFollowsClient(conn)
	return conn, client
}

func createFeedClient() (*grpc.ClientConn, pb.FeedClient) {
	const env = "FEED_SERVICE_HOST"
	host := os.Getenv(env)
	if host == "" {
		log.Fatalf("%s env var not set for skinny server", env)
	}
	addr := host + ":2012"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server could not connect to %s: %v", addr, err)
	}
	client := pb.NewFeedClient(conn)
	return conn, client
}

func createS2SFollowClient() (*grpc.ClientConn, pb.S2SFollowClient) {
	const env = "FOLLOW_ACTIVITY_SERVICE_HOST"
	host := os.Getenv(env)
	if host == "" {
		log.Fatalf("%s env var not set for skinny server", env)
	}
	addr := host + ":1922"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server could not connect to %s: %v", addr, err)
	}
	client := pb.NewS2SFollowClient(conn)
	return conn, client
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
	s2sFollowConn, s2sFollowClient := createS2SFollowClient()
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
