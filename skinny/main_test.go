package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/mux"
	"github.com/gorilla/sessions"
	"google.golang.org/grpc"

	pb "github.com/cpssd/rabble/services/proto"
)

const (
	fakeTitle = "fake"
)

type FeedFake struct {
	pb.FeedClient

	// The most recent postRequest
	rq *pb.FeedRequest
}

func (d *FeedFake) Get(_ context.Context, r *pb.FeedRequest, _ ...grpc.CallOption) (*pb.FeedResponse, error) {
	d.rq = r
	return &pb.FeedResponse{
		Results: []*pb.Post{{
			Title: fakeTitle,
		}},
	}, nil
}

type FollowsFake struct {
	pb.FollowsClient

	// The most recent LocalToAnyFollow
	rq *pb.LocalToAnyFollow
	// Most recent LocalToRss
	rrq *pb.LocalToRss
}

func (f *FollowsFake) RssFollowRequest(_ context.Context, r *pb.LocalToRss, _ ...grpc.CallOption) (*pb.FollowResponse, error) {
	f.rrq = r
	return &pb.FollowResponse{
		ResultType: pb.FollowResponse_OK,
	}, nil
}

type ArticleFake struct {
	pb.ArticleClient

	// The most recent NewArticle
	na *pb.NewArticle
}

func (a *ArticleFake) CreateNewArticle(_ context.Context, r *pb.NewArticle, _ ...grpc.CallOption) (*pb.NewArticleResponse, error) {
	a.na = r
	return &pb.NewArticleResponse{
		ResultType: pb.NewArticleResponse_OK,
		GlobalId:   "test_id",
	}, nil
}

type DatabaseFake struct {
	pb.DatabaseClient

	rq *pb.PostsRequest
}

func (d *DatabaseFake) Posts(_ context.Context, r *pb.PostsRequest, _ ...grpc.CallOption) (*pb.PostsResponse, error) {
	d.rq = r
	return &pb.PostsResponse{
		Results: []*pb.PostsEntry{{
			Title: fakeTitle,
		}},
	}, nil
}

func (f *FollowsFake) SendFollowRequest(_ context.Context, r *pb.LocalToAnyFollow, _ ...grpc.CallOption) (*pb.FollowResponse, error) {
	f.rq = r
	return &pb.FollowResponse{
		ResultType: pb.FollowResponse_OK,
	}, nil
}

type LDNormFake struct {
	pb.LDNormClient
}

func (l *LDNormFake) Normalise(_ context.Context, r *pb.NormaliseRequest, _ ...grpc.CallOption) (*pb.NormaliseResponse, error) {
	return &pb.NormaliseResponse{
		ResultType: pb.NormaliseResponse_OK,
		Normalised: r.Json,
	}, nil
}

func newTestServerWrapper() *serverWrapper {
	// TODO(iandioch): Fake/mock instead of using real dependencies
	r := mux.NewRouter()
	srv := &http.Server{}
	store := sessions.NewCookieStore([]byte("test"))
	s := &serverWrapper{
		router:       r,
		server:       srv,
		store:        store,
		shutdownWait: 20 * time.Second,
		database:     &DatabaseFake{},
		article:      &ArticleFake{},
		feed:         &FeedFake{},
		follows:      &FollowsFake{},
		s2sLike:      &LikeFake{},
		ldNorm:       &LDNormFake{},
	}
	s.setupRoutes()
	return s
}

func addFakeSession(s *serverWrapper, w http.ResponseWriter, r *http.Request) {
	session, _ := s.store.Get(r, "rabble-session")
	session.Values["handle"] = "jose"
	session.Save(r, w)
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
	jsonString := `{ "followed": "testuser", "follower": "jose" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("GET", "/c2s/follow", jsonBuffer)
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	addFakeSession(srv, res, req)
	srv.handleFollow()(res, req)
	if res.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %#v", res.Code)
	}
	var r pb.FollowResponse
	json.Unmarshal([]byte(res.Body.String()), &r)
	if r.ResultType != pb.FollowResponse_OK {
		t.Errorf("Expected FollowResponse_OK, got %#v", r.ResultType)
	}
}

func TestHandleFollowBadRequest(t *testing.T) {
	jsonString := `{ this is not json }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("GET", "/c2s/follow", jsonBuffer)
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	addFakeSession(srv, res, req)
	srv.handleFollow()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400 Bad Request, got %#v", res.Code)
	}
	var r pb.FollowResponse
	json.Unmarshal([]byte(res.Body.String()), &r)
	if r.ResultType != pb.FollowResponse_ERROR {
		t.Errorf("Expected FollowResponse_ERROR, got %#v", r.ResultType)
	}
}

func TestHandleFollowNotLoggedIn(t *testing.T) {
	jsonString := `{ "followed": "testuser", "follower": "jose" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("GET", "/c2s/follow", jsonBuffer)
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	srv.handleFollow()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400 Bad Request, got %#v", res.Code)
	}
	var r pb.FollowResponse
	json.Unmarshal([]byte(res.Body.String()), &r)
	if r.ResultType != pb.FollowResponse_ERROR {
		t.Errorf("Expected FollowResponse_ERROR, got %#v", r.ResultType)
	}
}

func TestHandleRssFollow(t *testing.T) {
	jsonString := `{ "follower": "testuser", "feed_url": "jose" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("POST", "/c2s/rss_follow", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	addFakeSession(srv, res, req)
	srv.handleRssFollow()(res, req)
	if res.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %#v", res.Code)
	}
	var r pb.FollowResponse
	json.Unmarshal([]byte(res.Body.String()), &r)
	if r.ResultType != pb.FollowResponse_OK {
		t.Errorf("Expected FollowResponse_OK, got %#v", r.ResultType)
	}
}

func TestHandleRssFollowBadRequest(t *testing.T) {
	jsonString := `{ this is not json }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("POST", "/c2s/rss_follow", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	addFakeSession(srv, res, req)
	srv.handleRssFollow()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400 Bad Request, got %#v", res.Code)
	}
	var r pb.FollowResponse
	json.Unmarshal([]byte(res.Body.String()), &r)
	if r.ResultType != pb.FollowResponse_ERROR {
		t.Errorf("Expected FollowResponse_ERROR, got %#v", r.ResultType)
	}
}

func TestHandleRssFollowNotLoggedIn(t *testing.T) {
	jsonString := `{ "follower": "testuser", "feed_url": "jose" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("GET", "/c2s/rss_follow", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	srv.handleRssFollow()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400 Bad Request, got %#v", res.Code)
	}
	var r pb.FollowResponse
	json.Unmarshal([]byte(res.Body.String()), &r)
	if r.ResultType != pb.FollowResponse_ERROR {
		t.Errorf("Expected FollowResponse_ERROR, got %#v", r.ResultType)
	}
}

func TestHandleCreateArticleSuccess(t *testing.T) {
	timeParseFormat := "2006-01-02T15:04:05.000Z"
	currentTimeString := time.Now().Format(timeParseFormat)
	jsonString := `{ "author": "jose", "body": "test post", "title": "test title", "creation_datetime": "` + currentTimeString + `" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("POST", "/test", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()
	addFakeSession(srv, res, req)
	srv.handleCreateArticle()(res, req)
	if res.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %#v", res.Code)
	}
	expectedString := "Created blog with title: test title and result type: 0\n"
	if res.Body.String() != expectedString {
		t.Errorf("Expected '"+expectedString+"' body, got %#v", res.Body.String())
	}
}

func TestHandleCreateArticleNotLoggedIn(t *testing.T) {
	timeParseFormat := "2006-01-02T15:04:05.000Z"
	currentTimeString := time.Now().Format(timeParseFormat)
	jsonString := `{ "author": "jose", "body": "test post", "title": "test title", "creation_datetime": "` + currentTimeString + `" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("POST", "/test", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()
	srv.handleCreateArticle()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400 Bad Request, got %#v", res.Code)
	}
}

func TestHandleCreateArticleBadJSON(t *testing.T) {
	jsonString := `{ author: "jose", "body": "test post", "title": "test title" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("POST", "/test", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	vars := map[string]string{
		"username": "testuser",
	}
	req = mux.SetURLVars(req, vars)
	srv := newTestServerWrapper()
	addFakeSession(srv, res, req)
	srv.handleCreateArticle()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400, got %#v", res.Code)
	}
	if res.Body.String() != "Invalid JSON\n" {
		t.Errorf("Expected 'Invalid JSON' body, got %#v", res.Body.String())
	}
}

func TestHandleCreateArticleBadCreationDatetime(t *testing.T) {
	jsonString := `{ "author": "jose", "body": "test post", "title": "test title", "creation_datetime": "never" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("POST", "/test", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()
	addFakeSession(srv, res, req)
	srv.handleCreateArticle()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400, got %#v", res.Code)
	}
	if res.Body.String() != "Invalid creation time\n" {
		t.Errorf("Expected 'Invalid creation time' body, got %#v", res.Body.String())
	}
}

func TestHandleCreateArticleOldCreationDatetime(t *testing.T) {
	jsonString := `{ "author": "jose", "body": "test post", "title": "test title", "creation_datetime": "2006-01-02T15:04:05.000Z" }`
	jsonBuffer := bytes.NewBuffer([]byte(jsonString))
	req, _ := http.NewRequest("POST", "/test", jsonBuffer)
	req.Header.Set("Content-Type", "application/json")
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()
	addFakeSession(srv, res, req)
	srv.handleCreateArticle()(res, req)
	if res.Code != http.StatusBadRequest {
		t.Errorf("Expected 400, got %#v", res.Code)
	}
	if res.Body.String() != "Old creation time\n" {
		t.Errorf("Expected 'Old creation time' body, got %#v", res.Body.String())
	}
}

func TestFeed(t *testing.T) {
	req, _ := http.NewRequest("GET", "/c2s/feed", nil)
	res := httptest.NewRecorder()
	srv := newTestServerWrapper()

	srv.handleFeed()(res, req)
	if res.Code != http.StatusOK {
		t.Errorf("Expected 200 OK, got %#v", res.Code)
	}

	var r []pb.Post
	if err := json.Unmarshal(res.Body.Bytes(), &r); err != nil {
		t.Fatalf("json.Unmarshal(%#v) unexpected error: %v", res.Body.String(), err)
	}

	if len(r) != 1 {
		t.Fatalf("Expected one result, got %v", len(r))
	}

	if r[0].Title != fakeTitle {
		t.Fatalf("Expected faked response, got %v", r[0].Title)
	}
}
