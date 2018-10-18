package main

import (
	"context"
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
)

const (
	staticAssets = "/repo/build_out/chump_dist"
)

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
    // greetingCards is the RPC client for talking to the GreetingCards service.
	greetingCards pb.GreetingCardsClient
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

// handleGreet sends an RPC to example_go_microservice with a card for the
// given name.
// TODO(#91): Remove example code when there are several real services being
// contacted from this server.
func (s *serverWrapper) handleGreet() http.HandlerFunc {
	host := os.Getenv("GO_SERVER_HOST")
	if host == "" {
		log.Fatal("GO_SERVER_HOST env var not set for skinny server.")
	}
	addr := host + ":8000"
	return func(w http.ResponseWriter, r *http.Request) {
		conn, err := grpc.Dial(addr, grpc.WithInsecure())
		if err != nil {
			log.Fatalf("Skinny server did not connect: %v", err)
		}
		defer conn.Close()

		c := pb.NewGreetingCardsClient(conn)

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

		ack, err := c.GetGreetingCard(ctx, gc)
		if err != nil {
			log.Fatalf("could not greet: %v", err)
		}
		log.Printf("Received ack card: %#v\n", ack.Letter)
		fmt.Fprintf(w, "Received: %#v", ack.Letter)
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
	r.HandleFunc("/api/", s.handleNotImplemented())

	// ActivityPub routes
	r.HandleFunc("/ap/", s.handleNotImplemented())
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
	s := &serverWrapper{
		router:        r,
		server:        srv,
		shutdownWait:  20 * time.Second,
		greetingCards: nil,
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
	ctx, cancel := context.WithTimeout(context.Background(), s.shutdownWait)
	defer cancel()

	// Waits for active connections to terminate, or until it hits the timeout.
	s.server.Shutdown(ctx)

	log.Printf("Stopping skinny server.\n")
	os.Exit(0)
}
