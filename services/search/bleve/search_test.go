package main

import (
	"context"
	"fmt"
	"testing"

	"github.com/blevesearch/bleve"
	pb "github.com/cpssd/rabble/services/proto"
	"google.golang.org/grpc"
)

const (
	LEN_TEST_POST = 10
)

type DBMock struct {
	t *testing.T
}

func (m *DBMock) buildFakePost(seed int64) *pb.PostsEntry {
	words := []string{
		"grandest", "greatest", "great", "cpssd", "flown",
		"tayne", "flower", "mangled", "mange", "typ0",
	}

	if seed < 0 || seed > (LEN_TEST_POST-1) {
		m.t.Fatalf("seed is not in range 0-%d", LEN_TEST_POST-1)
	}

	return &pb.PostsEntry{
		GlobalId:   seed,
		AuthorId:   seed % 4,
		Title:      fmt.Sprintf("%d", seed),
		Body:       fmt.Sprintf("<h4>%d</h4>\n<p> %s </p>", seed, words[seed]),
		MdBody:     fmt.Sprintf("# %d \n\n %s", seed, words[seed]),
		LikesCount: seed + LEN_TEST_POST + 10,
	}
}

func (m *DBMock) Posts(_ context.Context, in *pb.PostsRequest, opts ...grpc.CallOption) (*pb.PostsResponse, error) {
	if in.RequestType != pb.PostsRequest_FIND {
		return nil, fmt.Errorf("DBMock: should only use a FIND Request")
	}

	posts := []*pb.PostsEntry{}
	for i := 0; i < LEN_TEST_POST; i++ {
		posts = append(posts, m.buildFakePost(int64(i)))

	}

	m.t.Log(posts)

	return &pb.PostsResponse{Results: posts}, nil
}

func newMockedServer(t *testing.T) *Server {
	indexMapping := bleve.NewIndexMapping()
	index, err := bleve.NewMemOnly(indexMapping)
	if err != nil {
		t.Fatalf("Failed to init bleve index: %v", err)
	}

	dbMock := &DBMock{t}

	s := &Server{
		db:      dbMock,
		index:   index,
		idToDoc: map[int64]*pb.PostsEntry{},
	}

	return s
}

func TestCreateIndex(t *testing.T) {
	s := newMockedServer(t)
	s.createIndex()

	c, err := s.index.DocCount()
	if err != nil {
		t.Fatalf("Failed to count index: %v", err)
	}

	if c != LEN_TEST_POST {
		t.Fatalf("Not enough posts in index, got %v need %v", c, LEN_TEST_POST)
	}
}

func TestSearch(t *testing.T) {

	const (
		searchText   = "cpssd"
		foundArticle = 3
	)

	// TODO: expand search once more features are added
	s := newMockedServer(t)
	s.createIndex()

	r := &pb.SearchRequest{
		Query: &pb.SearchQuery{QueryText: searchText},
	}

	res, err := s.Search(context.Background(), r)
	if err != nil {
		t.Fatalf("Failed to search: %v", err)
	}

	if len(res.BResults) != 1 {
		t.Fatal("Expected to find single article")
	}

	if res.BResults[0].GlobalId != foundArticle {
		t.Fatalf("Failed to find article %d: %v", foundArticle, err)
	}

	if res.BResults[0].Title != fmt.Sprintf("%d", foundArticle) {
		t.Fatalf("Expected to find title to be \"%d\", got %#v", foundArticle, res.Results[0].Title)
	}
}
