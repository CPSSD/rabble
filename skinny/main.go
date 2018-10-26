package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"google.golang.org/grpc"

	pb "greetingCard"
	dbpb "proto/database"
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
	// shutdownWait specifies how long the server should wait when shutting
	// down for existing connections to finish before forcing a shutdown.
	shutdownWait time.Duration
	// greetingCardsConn is the underlying connection to the GreetingCards
	// service. This reference must be retained so it can by closed later.
	greetingCardsConn *grpc.ClientConn
	// greetingCards is the RPC client for talking to the GreetingCards
	// service.
	greetingCards pb.GreetingCardsClient

	databaseConn *grpc.ClientConn
	database     dbpb.DatabaseClient
}

func (s *serverWrapper) handleFeed() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		pr := &dbpb.PostsRequest{
			RequestType: dbpb.PostsRequest_FIND,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.database.Posts(ctx, pr)
		if err != nil {
			log.Fatalf("could not get feed: %v", err)
		}

		// TODO(devoxel): Remove SetEscapeHTML and properly handle that client side
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(false)

		err = enc.Encode(resp.Results)
		if err != nil {
			log.Printf("could not marshal blogs: %v", err)
			w.WriteHeader(500)
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

func (s *serverWrapper) handleIndex() http.HandlerFunc {
	indexPath := path.Join(staticAssets, "index.html")
	b, err := ioutil.ReadFile(indexPath)
	if err != nil {
		log.Fatal("could not find index.html: %v", err)
	}
	return func(w http.ResponseWriter, r *http.Request) {
		_, err := w.Write(b)
		if err != nil {
			log.Printf("handleIndex failed to write: %v\n", err)
		}
	}
}

func (s *serverWrapper) handleFollow() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		username := vars["username"]
		log.Printf("Requested to follow user %#v\n", username)
		fmt.Fprintf(w, "Followed %v\n", username)
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

		CreationDatetime, timeErr := time.Parse(timeParseFormat, t.CreationDatetime)
		if timeErr != nil {
			log.Printf("Invalid creation time\n")
			log.Printf("Error: %s\n", timeErr)
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Invalid creation time\n")
			return
		}

		timeSinceRequest := time.Since(CreationDatetime)
		if timeSinceRequest >= timeoutDuration || timeSinceRequest < 0 {
			log.Printf("Old creation time")
			w.WriteHeader(http.StatusBadRequest)
			fmt.Fprintf(w, "Old creation time\n")
			return
		}

		log.Printf("User %#v attempted to create a post with title: %v\n", t.Author, t.Title)
		fmt.Fprintf(w, "Created blog with title: %v\n", t.Title)
		// TODO(sailslick) send the response
	}
}

// handleGreet sends an RPC to example_go_microservice with a card for the
// given name.
// TODO(#91): Remove example code when there are several real services being
// contacted from this server.
func (s *serverWrapper) handleGreet() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		name := mux.Vars(r)["username"]
		msg := fmt.Sprintf("hello %#v", name)
		from := fmt.Sprintf("skinny-server-%v", name)
		gc := &pb.GreetingCard{
			Sender:        from,
			Letter:        msg,
			MoneyEnclosed: 123,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		ack, err := s.greetingCards.GetGreetingCard(ctx, gc)
		if err != nil {
			log.Fatalf("could not greet: %v", err)
		}
		log.Printf("Received ack card: %#v\n", ack.Letter)
		fmt.Fprintf(w, "Received: %#v", ack.Letter)
	}
}

// handleNewUser sends an RPC to the database service to create a user with the
// given info.
func (s *serverWrapper) handleNewUser() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		vars := r.URL.Query()
		// TODO(iandioch): Return error if parameters are missing.
		displayName := vars["display_name"][0]
		handle := vars["handle"][0]
		log.Printf("Trying to add new user %#v (%#v).\n", handle, displayName)
		u := &dbpb.UsersEntry{
			DisplayName: displayName,
			Handle:      handle,
		}
		ur := &dbpb.UsersRequest{
			Entry:       u,
			RequestType: dbpb.UsersRequest_INSERT,
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.database.Users(ctx, ur)
		if err != nil {
			log.Fatalf("could not greet: %v", err)
		}
		fmt.Fprintf(w, "Received: %#v", resp.Error)
		// TODO(iandioch): Return JSON with response status or error.
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
	r.HandleFunc("/@{username}/follow", s.handleFollow())
	r.HandleFunc("/@{username}/greet", s.handleGreet())

	// c2s routes
	r.HandleFunc("/c2s/create_article", s.handleCreateArticle())
	r.HandleFunc("/c2s/feed", s.handleFeed())
	r.HandleFunc("/c2s/new_user", s.handleNewUser())

	// ActivityPub routes
	r.HandleFunc("/ap/", s.handleNotImplemented())
}

func (s *serverWrapper) shutdown() {
	log.Printf("Stopping skinny server.\n")
	ctx, cancel := context.WithTimeout(context.Background(), s.shutdownWait)
	defer cancel()
	// Waits for active connections to terminate, or until it hits the timeout.
	s.server.Shutdown(ctx)

	s.greetingCardsConn.Close()
	s.databaseConn.Close()
}

func createGreetingCardsClient() (*grpc.ClientConn, pb.GreetingCardsClient) {
	host := os.Getenv("GO_SERVER_HOST")
	if host == "" {
		log.Fatal("GO_SERVER_HOST env var not set for skinny server.")
	}
	addr := host + ":8000"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect: %v", err)
	}
	return conn, pb.NewGreetingCardsClient(conn)
}

func createDatabaseClient() (*grpc.ClientConn, dbpb.DatabaseClient) {
	host := os.Getenv("DB_SERVICE_HOST")
	if host == "" {
		log.Fatal("DB_SERVICE_HOST env var not set for skinny server.")
	}
	addr := host + ":1798"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect: %v", err)
	}
	client := dbpb.NewDatabaseClient(conn)
	return conn, client
}

// buildServerWrapper sets up all necessary individual parts of the server
// wrapper, and returns one that is ready to run.
func buildServerWrapper() *serverWrapper {
	r := mux.NewRouter()
	srv := &http.Server{
		Addr: "0.0.0.0:1916",
		// Important to specify timeouts in order to prevent Slowloris attacks.
		WriteTimeout: time.Second * 15,
		ReadTimeout:  time.Second * 15,
		IdleTimeout:  time.Second * 60,
		Handler:      r,
	}
	greetingCardsConn, greetingCardsClient := createGreetingCardsClient()
	databaseConn, databaseClient := createDatabaseClient()
	s := &serverWrapper{
		router:            r,
		server:            srv,
		shutdownWait:      20 * time.Second,
		greetingCardsConn: greetingCardsConn,
		greetingCards:     greetingCardsClient,
		databaseConn:      databaseConn,
		database:          databaseClient,
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
