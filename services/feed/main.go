package main

import (
	"context"
	"log"
	"net"

	"github.com/golang/protobuf/ptypes/empty"
	"google.golang.org/grpc"

	dbpb "proto/database"
	pb "proto/feed"
)

type server struct{}

func (s *server) Get(ctx context.Context, r *pb.FeedRequest) (*pb.FeedResponse, error) {
	d := &dbpb.PostsEntry{Author: "wow"}
	e := &pb.Post{Author: d.Author}
	return &pb.FeedResponse{
		Results: []*pb.Post{e},
	}, nil
}

func (s *server) GetAll(ctx context.Context, _ *empty.Empty) (*pb.FeedResponse, error) {
	d := &dbpb.PostsEntry{Author: "wow"}
	e := &pb.Post{Author: d.Author}
	return &pb.FeedResponse{
		Results: []*pb.Post{e},
	}, nil
}

func main() {
	lis, err := net.Listen("tcp", ":2012")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	grpcSrv := grpc.NewServer()
	pb.RegisterFeedServer(grpcSrv, &server{})
	grpcSrv.Serve(lis)
}
