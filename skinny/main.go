package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
)

// serverWrapper encapsulates the dependencies and config values of
// the server into one struct. Server endpoint handlers hang off of
// this struct and can access their dependencies through it.
// See https://medium.com/statuscode/how-i-write-go-http-services-after-seven-years-37c208122831
// for rationale and further explanation.
type serverWrapper struct {
	router *mux.Router
	server *http.Server
	// Specifies how long the server should wait when shutting down
	// for existing connections to finish before forcing a shutdown.
	shutdownWait time.Duration
}

// Returns a http.HandlerFunc with a 501 Not Implemented error.
func (s *serverWrapper) handleNotImplemented() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		http.Error(w,
            http.StatusText(http.StatusNotImplemented),
			http.StatusNotImplemented)
	}
}

// setupRoutes specifies the routing of all endpoints on the server.
// Centralised routing config allows easier debugging of a specific
// endpoint, as the code handling it can be looked up here.
// The server uses mux for routing. See instructions and examples for
// mux at https://www.gorillatoolkit.org/pkg/mux .
// TODO(iandioch): Move setupRoutes() to its own file if/when it gets
// too big.
func (s *serverWrapper) setupRoutes() {
	log.Printf("Setting up routes on skinny server.\n")
	r := s.router
	r.HandleFunc("/", s.handleNotImplemented())
}

// Set up all necessary individual parts of the server wrapper,
// and return one that is ready to run.
func buildServerWrapper() *serverWrapper {
	r := mux.NewRouter()
	srv := &http.Server{
		Addr: "0.0.0.0:1916",
		// Important to specify timeouts in order to prevent
		// Slowloris attacks.
		WriteTimeout: time.Second * 15,
		ReadTimeout:  time.Second * 15,
		IdleTimeout:  time.Second * 60,
		Handler:      r,
	}
	s := &serverWrapper{r, srv, 20 * time.Second}
	s.setupRoutes()
	return s
}

func main() {
	log.Printf("Starting skinny server.\n")
	s := buildServerWrapper()

	// The following code is partially taken from this link:
	// https://github.com/gorilla/mux#graceful-shutdown
	// It lays out a way for a server to gracefully shutdown
	// when a SIGINT (Ctrl+C) or SIGTERM (kill) is received.
	// See also: https://gobyexample.com/signals

	go func() {
		if err := s.server.ListenAndServe(); err != nil {
			log.Println(err)
		}
	}()

	// Accept graceful shutdowns when quit via SIGINT or SIGTERM.
	// Other signals (eg. SIGKILL, SIGQUIT) will not be caught.
	// Docker sends a SIGTERM on shutdown.
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)

	// Block until we receive signal.
	<-c
	ctx, cancel := context.WithTimeout(context.Background(), s.shutdownWait)
	defer cancel()

	// Waits for active connections to terminate, or until it hits
	// the timeout.
	s.server.Shutdown(ctx)

	log.Printf("Stopping skinny server.\n")
	os.Exit(0)
}
