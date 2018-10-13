package main

import (
    "log"
    "net/http"

    "github.com/gorilla/mux"
)

type server struct {
    router *mux.Router
}

func noopHandler(w http.ResponseWriter, r *http.Request) {
    return
}

func (s *server) setupRoutes() {
    s.router.HandleFunc("/", noopHandler)
}

func main() {
	log.Printf("Starting skinny web server.\n")
    r := mux.NewRouter()
    server := &server{r}
    server.setupRoutes()
}
