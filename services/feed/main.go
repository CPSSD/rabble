package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"google.golang.org/grpc"

	dbpb "github.com/cpssd/rabble/services/database/proto"
	pb "github.com/cpssd/rabble/services/feed/proto"
)

// convertDBToFeed converts PostsResponses to FeedResponses.
// Hopefully this will removed once we fix proto building.
func convertDBToFeed(p *dbpb.PostsResponse) *pb.FeedResponse {
	fp := &pb.FeedResponse{}
	for _, r := range p.Results {
		np := &pb.Post{
			GlobalId:         r.GlobalId,
			Author:           r.Author,
			Title:            r.Title,
			Body:             r.Body,
			CreationDatetime: r.CreationDatetime,
		}
		fp.Results = append(fp.Results, np)
	}
	return fp
}

type server struct {
	db dbpb.DatabaseClient
}

func (s *server) Get(ctx context.Context, r *pb.FeedRequest) (*pb.FeedResponse, error) {
	pr := &dbpb.PostsRequest{
		RequestType: dbpb.PostsRequest_FIND,
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	resp, err := s.db.Posts(ctx, pr)
	if err != nil {
		return nil, fmt.Errorf("feed.Get failed: db.Posts(%v) error: %v", *pr, err)
	}

	return convertDBToFeed(resp), nil
}

func newServer(c *grpc.ClientConn) *server {
	db := dbpb.NewDatabaseClient(c)
	return &server{db: db}
}

func main() {
	log.Print("Starting feed")
	lis, err := net.Listen("tcp", ":2012")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	host := os.Getenv("DB_SERVICE_HOST")
	if host == "" {
		log.Fatal("DB_SERVICE_HOST env var not set for skinny server.")
	}
	addr := host + ":1798"

	c, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Could not connect to database: %v", err)
	}
	defer c.Close()

	grpcSrv := grpc.NewServer()
	pb.RegisterFeedServer(grpcSrv, newServer(c))
	grpcSrv.Serve(lis)
}
