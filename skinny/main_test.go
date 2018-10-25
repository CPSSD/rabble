package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/mux"

	dbpb "proto/database"
)

func newTestServerWrapper() *serverWrapper {
	// TODO(iandioch): Fake/mock instead of using real dependencies
	r := mux.NewRouter()
	srv := &http.Server{}
	s := &serverWrapper{
		router:            r,
		server:            srv,
		shutdownWait:      20 * time.Second,
		greetingCardsConn: nil,
		greetingCards:     nil,
	}
	s.setupRoutes()
	return s
}

func TestHandleNotImplemented(t *testing.T) {
	req, _ := http.NewRequest("GET", "/test", nil)
	res := httptest.NewRecorder()
	newTestServerWrapper().handleNotImplemented()(res, req)

	if res.Code != http.StatusNotImplemented {
		t.Errorf("Expected 501 Not Implemented, got %#v", res.Code)
	}
	if res.Body.String() != "Not Implemented\n" {
		t.Errorf("Expected 'Not Implemented' body, got %#v", res.Body.String())
	}
}

func TestHandleFollow(t *testing.T) {
	req, _ := http.NewRequest("GET", "/test", nil)
	res := httptest.NewRecorder()
	vars := map[string]string{
		"username": "testuser",
	}
	req = mux.SetURLVars(req, vars)
	newTestServerWrapper().handleFollow()(res, req)
	if res.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %#v", res.Code)
	}
	if res.Body.String() != "Followed testuser\n" {
		t.Errorf("Expected 'Followed testuser' body, got %#v", res.Body.String())
	}
}

func TestFeed(t *testing.T) {
	req, _ := http.NewRequest("GET", "/c2s/feed", nil)
	res := httptest.NewRecorder()
	newTestServerWrapper().handleFeed()(res, req)

	if res.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %#v", res.Code)
	}

	var r []dbpb.PostsEntry
	if err := json.Unmarshal(res.Body.Bytes(), &r); err != nil {
		t.Fatalf("json.Unmarshal(%#v) unexpected error: %v", res.Body.String(), err)
	}

	// No need to test these in depth right now, will expand tests when
	// it's talking to the server
	if len(r) != 2 {
		t.Fatalf("Expected two results, got %v", len(r))
	}

	if !strings.Contains(res.Body.String(), "<") {
		t.Fatalf("Expecting %v to unescape angle brackets", res.Body.String())
	}
}
