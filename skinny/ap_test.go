package main

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"
)

func setupFakeActorInboxRoutes(s *serverWrapper) {
	s.actorInboxRouter = map[string]http.HandlerFunc{
		"create": func(w http.ResponseWriter, r *http.Request) {},
		"follow": func(w http.ResponseWriter, r *http.Request) {},
	}
}

func TestActorInboxRouting(t *testing.T) {
	srv := newTestServerWrapper()
	setupFakeActorInboxRoutes(srv)

	tests := []string{
		`{ "type": "create" }`,
		`{ "type": "follow" }`,
		`{ "type": "Create" }`,
		`{ "type": "Follow" }`,
	}

	for _, test := range tests {
		r := bytes.NewBufferString(test)
		req, _ := http.NewRequest("POST", "/ap/testuser/", r)
		res := httptest.NewRecorder()
		srv.handleActorInbox()(res, req)

		if res.Code != http.StatusOK {
			t.Errorf("Expected 200 OK, got %#v", res.Code)
		}
	}
}
