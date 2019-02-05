package main

import (
	"context"
	"log"
	"net"
	"os"
	"strconv"

	pb "github.com/cpssd/rabble/services/proto"
	"google.golang.org/grpc"

	"github.com/blevesearch/bleve"
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

type PostGetter interface {
	Posts(ctx context.Context, in *pb.PostsRequest, opts ...grpc.CallOption) (*pb.PostsResponse, error)
}

type Server struct {
	dbConn *grpc.ClientConn
	db     PostGetter

	index bleve.Index
	// idToDoc is a hack to speed up article lookups.
	// TODO(devoxel): Figure out how to this using bleve.Index
	idToDoc map[int64]*pb.PostsEntry
}

func newServer() *Server {
	dbConn, dbClient := createDatabaseClient()

	indexMapping := bleve.NewIndexMapping()
	index, err := bleve.NewMemOnly(indexMapping)
	if err != nil {
		log.Fatalf("Failed to init bleve index: %v", err)
	}

	s := &Server{
		db:      dbClient,
		dbConn:  dbConn,
		index:   index,
		idToDoc: map[int64]*pb.PostsEntry{},
	}

	s.createIndex()
	return s
}

func (s *Server) createIndex() {
	req := &pb.PostsRequest{
		RequestType: pb.PostsRequest_FIND,
	}

	res, err := s.db.Posts(context.Background(), req)
	if err != nil {
		log.Fatalf("Failed to create index: %v", err)
	}

	for _, blog := range res.Results {
		id := strconv.FormatInt(blog.GlobalId, 10)
		s.index.Index(id, blog)
		s.idToDoc[blog.GlobalId] = blog
	}
}

func (s *Server) Search(ctx context.Context, r *pb.SearchRequest) (*pb.SearchResponse, error) {
	q := bleve.NewMatchQuery(r.Query.QueryText)
	search := bleve.NewSearchRequest(q)
	searchRes, err := s.index.Search(search)
	if err != nil {
		log.Printf("Failed to search index: %v", err)
		return nil, err
	}

	resp := &pb.SearchResponse{}
	// TODO(devoxel) Add a search limit & pagination
	for _, hit := range searchRes.Hits {
		id, err := strconv.ParseInt(hit.ID, 10, 64)
		if err != nil {
			log.Printf("Bad id (%s) in search index: %v", hit.ID, err)
			continue
		}

		doc, exists := s.idToDoc[id]
		if !exists {
			log.Printf("WARNING: doc found in search does not exist for id: %d", id)
		}

		resp.Results = append(resp.Results, doc)
	}

	return resp, nil
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
