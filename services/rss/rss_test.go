package main

import (
	"context"
	"testing"

	pb "github.com/cpssd/rabble/services/proto"
	"google.golang.org/grpc"
)

type DatabaseFake struct {
	pb.DatabaseClient

	rq *pb.PostsRequest
}

func newTestServerWrapper() *serverWrapper {
	// TODO(iandioch): Fake/mock instead of using real dependencies
	sw := &serverWrapper{
		server:   &grpc.Server{},
		db: &DatabaseFake{},
	}
	return sw
}

func TestNewRssFollow(t *testing.T) {
	sw := newTestServerWrapper()

	req := &pb.NewRssFeed{
    RssUri: "https://news.ycombinator.com/rss",
    Follower: "Johnny",
  }

	r, err := sw.NewRssFollow(context.Background(), req)
	if err != nil {
		t.Fatalf("NewRssFollow(%v), unexpected error: %v", req.RssUri , err)
	}

  if r.ResultType != pb.RssResponse_ACCEPTED {
    t.Fatalf("NewRssFollow(%v), received non accept result_type: %v", req.RssUri , r.ResultType)
  }
}
