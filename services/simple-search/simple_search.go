package main

import (
	"context"
	"log"
	"net"
	"os"

	utils "github.com/cpssd/rabble/services/utils"
	pb "github.com/cpssd/rabble/services/proto"
	"google.golang.org/grpc"
)

func createDatabaseClient() (*grpc.ClientConn, pb.DatabaseClient) {
	// TODO(devoxel): would be nice to use skinny.grpcConn here
	host := os.Getenv("DB_SERVICE_HOST")
	if host == "" {
		log.Fatal("DB_SERVICE_HOST env var not set for search service.")
	}
	addr := host + ":1798"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Search server did not connect to db: %v", err)
	}
	client := pb.NewDatabaseClient(conn)
	return conn, client
}

type Server struct {
	dbConn *grpc.ClientConn
	db     pb.DatabaseClient
}

func newServer() *Server {
	dbConn, dbClient := createDatabaseClient()

	return &Server{
		db:     dbClient,
		dbConn: dbConn,
	}
}

func (s *Server) Search(ctx context.Context, r *pb.SearchRequest) (*pb.SearchResponse, error) {
	log.Printf("Query: %s\n", r.Query)
	if r.Query == "" {
		return &pb.SearchResponse{}, nil
	}

	sReq := &pb.SearchRequest{
		Query: r.Query,
	}

	ctx, cancel := context.WithTimeout(ctx, time.Second)
	defer cancel()

	resp, err := s.db.SearchArticles(ctx, sReq)
	if err != nil {
		return nil, fmt.Errorf("simple-search.SearchArticles failed: db.Posts(%v) error: %v", *pr, err)
	}
	sr := &pb.SearchResponse{}
	sr.Results = utils.ConvertDBToFeed(ctx, resp, s.db)

	return sr, nil
}

func main() {
	log.Print("Starting simple-search service.")

	lis, err := net.Listen("tcp", ":1886")
	if err != nil {
		log.Fatalf("failed to listen to 0.0.0.0:1886: %v", err)
	}

	grpcSrv := grpc.NewServer()
	pb.RegisterSearchServer(grpcSrv, newServer())
	grpcSrv.Serve(lis)
}
