package main

import (
	"log"
	"net/http"
	"time"

	"github.com/gorilla/mux"
)

type serverWrapper struct {
	router *mux.Router
	server *http.Server
}

func noopHandler(w http.ResponseWriter, r *http.Request) {
	return
}

func (s *serverWrapper) setupRoutes() {
	log.Printf("Setting up routes on skinny server.\n")
	r := s.router
	r.HandleFunc("/", noopHandler)
}

// Set up all necessary individual parts of the server wrapper,
// and return one that is ready to run.
func buildServerWrapper() *serverWrapper {
	r := mux.NewRouter()
	srv := &http.Server{
		Addr: "0.0.0.0:1916",
		// Important to specify in order to prevent Slowloris attacks.
		WriteTimeout: time.Second * 15,
		ReadTimeout:  time.Second * 15,
		IdleTimeout:  time.Second * 60,
		Handler:      r,
	}
	s := &serverWrapper{r, srv}
	s.setupRoutes()
	return s
}

func main() {
	log.Printf("Starting skinny server.\n")
	s := buildServerWrapper()
	go func() {
		if err := s.server.ListenAndServe(); err != nil {
			log.Println(err)
		}
	}()
}
