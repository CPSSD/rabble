package main

import (
	"context"
	"testing"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/mmcdole/gofeed"
	"google.golang.org/grpc"
)

type DatabaseFake struct {
	pb.DatabaseClient

	rq *pb.PostsRequest
}

func newTestServerWrapper() *serverWrapper {
	// TODO(iandioch): Fake/mock instead of using real dependencies

	fp := gofeed.NewParser()
	sw := &serverWrapper{
		server:   &grpc.Server{},
		db: &DatabaseFake{},
		feedParser: fp,
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
		t.Fatalf("NewRssFollow(%v), unexpected error: %v", req.RssUrl , err)
	}

  if r.ResultType != pb.NewRssFeedResponse_ACCEPTED {
    t.Fatalf("NewRssFollow(%v), received non accept result_type: %v", req.RssUrl , r.ResultType)
  }
}
