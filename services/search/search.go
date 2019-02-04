package main

import (
	"context"
	"log"
	"net"
	"os"

	pb "github.com/cpssd/rabble/services/proto"
	"google.golang.org/grpc"

	"github.com/blevesearch/bleve"
	"github.com/blevesearch/bleve/mapping"
)

func createDatabaseClient() (*grpc.ClientConn, pb.DatabaseClient) {
	// TODO(devoxel): would be nice to use skinny.grpcConn here
	host := os.Getenv("DB_SERVICE_HOST")
	if host == "" {
		log.Fatal("DB_SERVICE_HOST env var not set for rss service.")
	}
	addr := host + ":1798"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Rss server did not connect to db: %v", err)
	}
	client := pb.NewDatabaseClient(conn)
	return conn, client
}

type Server struct {
	dbConn *grpc.ClientConn
	db     pb.DatabaseClient

	index *mapping.IndexMappingImpl
}

func newServer() *Server {
	dbConn, dbClient := createDatabaseClient()

	return &Server{
		db:     dbClient,
		dbConn: dbConn,
		index:  bleve.NewIndexMapping(),
	}
}

func (s *Server) PlainTextSearch(ctx context.Context, r *pb.SearchRequest) (*pb.SearchResponse, error) {
	return &pb.SearchResponse{}, nil
}

func (s *Server) Search(ctx context.Context, r *pb.SearchRequest) (*pb.SearchResponse, error) {
	return s.PlainTextSearch(ctx, r)
}

func main() {
	log.Print("Starting search service.")

	lis, err := net.Listen("tcp", ":1886")
	if err != nil {
		log.Fatalf("failed to listen to 0.0.0.0:1886: %v", err)
	}

	grpcSrv := grpc.NewServer()
	pb.RegisterSearchServer(grpcSrv, newServer())
	grpcSrv.Serve(lis)
}
