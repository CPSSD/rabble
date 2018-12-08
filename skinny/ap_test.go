package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"google.golang.org/grpc"

	pb "github.com/cpssd/rabble/services/proto"
)

func setupFakeActorInboxRoutes(t *testing.T, s *serverWrapper) {
	const bodyReadErr = "Failed to read body twice: %v"
	unmarshal := func(r *http.Request) {
		d := json.NewDecoder(r.Body)
		var a activity

		if err := d.Decode(&a); err != nil {
			t.Errorf("Failed to re-read activity: %v", err)
		}
	}

	s.actorInboxRouter = map[string]http.HandlerFunc{
		"create": func(w http.ResponseWriter, r *http.Request) {
			unmarshal(r)
		},
		"follow": func(w http.ResponseWriter, r *http.Request) {
			unmarshal(r)
		},
	}
}

func TestActorInboxRouting(t *testing.T) {
	srv := newTestServerWrapper()
	setupFakeActorInboxRoutes(t, srv)

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

type LikeFake struct {
	pb.S2SLikeClient

	rq *pb.ReceivedLikeDetails
}

func (d *LikeFake) ReceiveLikeActivity(_ context.Context, r *pb.ReceivedLikeDetails, _ ...grpc.CallOption) (*pb.LikeResponse, error) {
	d.rq = r
	return &pb.LikeResponse{
		ResultType: pb.LikeResponse_OK,
	}, nil
}

func TestsHandleLikeActivity(t *testing.T) {
	jsonString := `{
		"type": "Like",
		"@context": "http://test.com/test",
		"object": "http://rabble.com/@abc/123",
		"actor": {
			"id": "http://rabble.com/@def",
			"type": "Person"
		}
	}`
	req, _ := http.NewRequest("GET", "/ap/@abc/inbox", bytes.NewBuffer([]byte(jsonString)))
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	srv.handleLikeActivity()(res, req)
	if res.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %#v", res.Code)
	}
}
