package main

import (
	"context"
	"fmt"
	"testing"

	"github.com/blevesearch/bleve"
	pb "github.com/cpssd/rabble/services/proto"
	util "github.com/cpssd/rabble/services/utils"
	"github.com/golang/protobuf/ptypes"
	"google.golang.org/grpc"
)

const (
	LEN_TEST_POST = 15
	MAX_TEST_POST = 20
)

func buildFakePost(t *testing.T, seed int64) *pb.PostsEntry {
	words := []string{
		"grandest", "greatest", "great", "cpssd", "flown",
		"tayne", "flower", "mangled", "mange", "typ0",
		"grandayy", "dolandark", "scrubs", "geralt", "rivia",
		"caleb", "jester", "nott", "fjord", "yasha", "beau", "cad",
	}

	if len(words) < MAX_TEST_POST {
		t.Fatalf("words array exceeds max of %d", MAX_TEST_POST)
	}

	if seed < 0 || seed > (MAX_TEST_POST-1) {
		t.Fatalf("seed is not in range 0-%d", MAX_TEST_POST-1)
	}

	now := ptypes.TimestampNow()

	return &pb.PostsEntry{
		GlobalId:         seed,
		AuthorId:         seed % 4,
		Title:            fmt.Sprintf("TITLE %d", seed),
		Body:             fmt.Sprintf("HTML <h4>%d</h4>\n<p> %s </p>", seed, words[seed]),
		MdBody:           fmt.Sprintf("MARKDOWN # %d \n\n %s", seed, words[seed]),
		LikesCount:       seed + MAX_TEST_POST + 10,
		CreationDatetime: now,
	}
}

type DBMock struct {
	t *testing.T
}

func (m *DBMock) Posts(_ context.Context, in *pb.PostsRequest, opts ...grpc.CallOption) (*pb.PostsResponse, error) {
	if in.RequestType != pb.PostsRequest_FIND {
		return nil, fmt.Errorf("DBMock: should only use a FIND Request")
	}

	posts := []*pb.PostsEntry{}
	for i := 0; i < LEN_TEST_POST; i++ {
		posts = append(posts, buildFakePost(m.t, int64(i)))
	}

	return &pb.PostsResponse{Results: posts}, nil
}

func (m *DBMock) Users(_ context.Context, in *pb.UsersRequest, opts ...grpc.CallOption) (*pb.UsersResponse, error) {
	if in.RequestType != pb.UsersRequest_FIND {
		return nil, fmt.Errorf("DBMock: should only use a FIND Request")
	}

	u := &pb.UsersEntry{
		Handle:      fmt.Sprintf("HANDLE %d", in.Match.GlobalId),
		DisplayName: fmt.Sprintf("DISPLAY_NAME %d", in.Match.GlobalId),
		GlobalId:    in.Match.GlobalId,
	}

	return &pb.UsersResponse{
		Results: []*pb.UsersEntry{u},
	}, nil
}

func newMockedServer(t *testing.T) *Server {
	indexMapping := createIndexMapping()
	index, err := bleve.NewMemOnly(indexMapping)
	if err != nil {
		t.Fatalf("Failed to init bleve index: %v", err)
	}

	dbMock := &DBMock{t}

	s := &Server{
		db:      dbMock,
		index:   index,
		idToDoc: map[int64]*pb.Post{},
	}

	return s
}

func TestCreateIndex(t *testing.T) {
	s := newMockedServer(t)
	s.initIndex()

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
	s.initIndex()

	r := &pb.SearchRequest{
		Query: &pb.SearchQuery{QueryText: searchText},
	}

	res, err := s.Search(context.Background(), r)
	if err != nil {
		t.Fatalf("Failed to search: %v", err)
	}

	if len(res.Results) != 1 {
		t.Fatal("Expected to find single article")
	}

	if res.Results[0].GlobalId != foundArticle {
		t.Fatalf("Failed to find article %d: %v", foundArticle, err)
	}

	if res.Results[0].Title != fmt.Sprintf("TITLE %d", foundArticle) {
		t.Fatalf("Expected to find title to be \"TITLE %d\", got %#v",
			foundArticle, res.Results[0].Title)
	}
}

func TestFieldsSearch(t *testing.T) {
	tests := []struct {
		query      string
		lenResults int
	}{
		{
			query:      "TITLE",
			lenResults: LEN_TEST_POST,
		},
		{
			query:      "HTML",
			lenResults: LEN_TEST_POST,
		},
		{
			query:      "HANDLE",
			lenResults: LEN_TEST_POST,
		},
		{
			query:      "DISPLAY_NAME",
			lenResults: 0,
		},
		{
			query:      "MARKDOWN",
			lenResults: 0,
		},
	}

	s := newMockedServer(t)
	s.initIndex()

	for _, tcase := range tests {
		r := &pb.SearchRequest{
			Query: &pb.SearchQuery{QueryText: tcase.query},
		}

		res, err := s.Search(context.Background(), r)
		if err != nil {
			t.Fatalf("Failed to search: %v", err)
		}

		if len(res.Results) != tcase.lenResults {
			t.Fatalf("Expected to find %d results for search %s, found %d",
				tcase.lenResults, tcase.query, len(res.Results))
		}
	}
}

func TestIndex(t *testing.T) {
	s := newMockedServer(t)
	s.initIndex()

	checkSearch := func(results int) {
		r := &pb.SearchRequest{
			Query: &pb.SearchQuery{QueryText: "HTML"},
		}
		res, err := s.Search(context.Background(), r)
		if err != nil {
			t.Fatalf("Failed to search: %v", err)
		}

		if len(res.Results) != results {
			t.Fatalf("Expcted to find %d posts, got %v",
				results, len(res.Results))
		}
	}

	currentId := LEN_TEST_POST
	addToIndex := func() {
		entry := &pb.PostsResponse{
			Results: []*pb.PostsEntry{
				buildFakePost(t, int64(currentId)),
			},
		}
		post := util.ConvertDBToFeed(context.Background(), entry, s.db)

		i := &pb.IndexRequest{Post: post[0]}
		res, err := s.Index(context.Background(), i)
		if err != nil {
			t.Fatalf("Failed to call Index(%v): %v", *i, err)
		}
		if res.ResultType != pb.IndexResponse_OK {
			t.Fatalf("Failed to call Index(%v): %v", *i, res.Error)
		}
		currentId += 1
	}

	checkSearch(LEN_TEST_POST)
	addToIndex()
	checkSearch(LEN_TEST_POST + 1)
	addToIndex()
	checkSearch(LEN_TEST_POST + 2)
}
