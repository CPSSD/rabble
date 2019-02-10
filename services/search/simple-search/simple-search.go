package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	utils "github.com/cpssd/rabble/services/utils"
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

	x := &Server{
		db:     dbClient,
		dbConn: dbConn,
	}
	x.CreateIndices()
	return x
}
func (s *Server) CreateIndices() {
	log.Println("Creating Indices\n")
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*2)
	defer cancel()
	_, postErr := s.db.CreatePostsIndex(ctx, &pb.DatabaseSearchRequest{})
	if postErr != nil {
		log.Fatalf("simple-search.CreatePostsIndex failed. error: %v", postErr)
	}
	_, userErr := s.db.CreateUsersIndex(ctx, &pb.DatabaseSearchRequest{})
	if userErr != nil {
		log.Fatalf("simple-search.CreateUsersIndex failed. error: %v", userErr)
	}
}

func (s *Server) Index(ctx context.Context, r *pb.IndexRequest) (*pb.IndexResponse, error) {
	// hey there, i'm all good, i dont need to index, thanks for asking
	return &pb.IndexResponse{}, nil
}

func (s *Server) Search(ctx context.Context, r *pb.SearchRequest) (*pb.SearchResponse, error) {
	log.Printf("Query: %s\n", r.Query.QueryText)
	if r.Query.QueryText == "" {
		log.Printf("Empty query\n")
		return &pb.SearchResponse{}, nil
	}

	sReq := &pb.DatabaseSearchRequest{
		Query:        r.Query.QueryText,
		UserGlobalId: r.UserGlobalId,
	}

	ctx, cancel := context.WithTimeout(ctx, time.Second*2)
	defer cancel()

	pResp, pErr := s.db.SearchArticles(ctx, sReq)
	if pErr != nil {
		return nil, fmt.Errorf("simple-search.Search failed: db.SearchArticles(%v) error: %v", *sReq, pErr)
	}
	sr := &pb.SearchResponse{}
	sr.Results = utils.ConvertDBToFeed(ctx, pResp, s.db)

	uResp, uErr := s.db.SearchUsers(ctx, sReq)
	if uErr != nil {
		return nil, fmt.Errorf("simple-search.Search failed: db.SearchUsers(%v) error: %v", *sReq, uErr)
	}
	sr.UResults = utils.ConvertDBToUsers(ctx, uResp, s.db)

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
