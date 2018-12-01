package main

import (
	"context"
	"testing"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/mmcdole/gofeed"
	"google.golang.org/grpc"
)

const (
	fakeTitle = "fake test title"
)

type gofeedFake struct {
	gofeed.Parser
}

func (d *gofeedFake) ParseURL(url string) (*gofeed.Feed, error) {
	return &gofeed.Feed{
		Title: fakeTitle,
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
		GlobalId:   "test id",
	}, nil
}

type DatabaseFake struct {
	pb.DatabaseClient

	ur *pb.UsersRequest
}

func (d *DatabaseFake) Users(_ context.Context, r *pb.UsersRequest, _ ...grpc.CallOption) (*pb.UsersResponse, error) {
	d.ur = r
	ue := &pb.UsersEntry{
		Handle: "test/rss",
		GlobalId: 1,
	}
	return &pb.UsersResponse{
		ResultType: pb.UsersResponse_OK,
		Results:    []*pb.UsersEntry{ue},
	}, nil
}

func newTestServerWrapper() *serverWrapper {
	// TODO(iandioch): Fake/mock instead of using real dependencies

	sw := &serverWrapper{
		server:     &grpc.Server{},
		art:        &ArticleFake{},
		db:         &DatabaseFake{},
		feedParser: &gofeedFake{},
	}
	return sw
}

func TestNewRssFollow(t *testing.T) {
	sw := newTestServerWrapper()

	req := &pb.NewRssFeed{
		RssUrl: "https://news.ycombinator.com/rss",
	}

	r, err := sw.NewRssFollow(context.Background(), req)
	if err != nil {
		t.Fatalf("NewRssFollow(%v), unexpected error: %v", req.RssUrl, err)
	}

	if r.ResultType != pb.NewRssFeedResponse_ACCEPTED {
		t.Fatalf("NewRssFollow(%v), received non accept result_type: %v", req.RssUrl, r.ResultType)
	}
}
