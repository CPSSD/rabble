package main

import (
	"context"
	"errors"
	"log"
	"net"
	"os"
	"strconv"

	pb "github.com/cpssd/rabble/services/proto"
	util "github.com/cpssd/rabble/services/utils"

	"github.com/blevesearch/bleve"
	"github.com/blevesearch/bleve/mapping"
	"google.golang.org/grpc"
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

func createIndexMapping() mapping.IndexMapping {
	indexMapping := bleve.NewIndexMapping()
	doc := mapping.NewDocumentStaticMapping()

	text := mapping.NewTextFieldMapping()
	// TODO(devoxel): figure out field mapping for creation timestamp
	doc.AddFieldMappingsAt("body", text)
	doc.AddFieldMappingsAt("title", text)
	doc.AddFieldMappingsAt("author", text)

	// This sets the document mapping such that any document added uses
	// the document mapping defined above. Since it's static, this only
	// searches explicitly declared fields.
	indexMapping.AddDocumentMapping("_default", doc)

	// TODO(devoxel): Ideally, we should annotate a PostsEntry type with
	// the Type() functions, allowing more complex search conversions
	// This allows custom character filters by type, or custom language
	// analysis by type.
	return indexMapping
}

func createIndex() (bleve.Index, error) {
	indexMapping := createIndexMapping()
	path := os.Getenv("INDEX_PATH")
	if path == "" {
		log.Print("INDEX_PATH not found, using memory index.")
		return bleve.NewMemOnly(indexMapping)
	}

	return bleve.New(path, indexMapping)
}

type PostGetter interface {
	Posts(ctx context.Context, in *pb.PostsRequest, opts ...grpc.CallOption) (*pb.PostsResponse, error)
	// Users is required for util.ConvertDBToFeed
	Users(ctx context.Context, in *pb.UsersRequest, opts ...grpc.CallOption) (*pb.UsersResponse, error)
}

type Server struct {
	dbConn *grpc.ClientConn
	db     PostGetter

	index bleve.Index
	// idToDoc is a hack to speed up article lookups.
	// TODO(devoxel): Figure out how to this using bleve.Index
	idToDoc map[int64]*pb.Post
}

func newServer() *Server {
	dbConn, dbClient := createDatabaseClient()
	index, err := createIndex()
	if err != nil {
		log.Fatalf("Failed to init bleve index: %v", err)
	}

	s := &Server{
		db:      dbClient,
		dbConn:  dbConn,
		index:   index,
		idToDoc: map[int64]*pb.Post{},
	}

	s.initIndex()
	return s
}

func (s *Server) addToIndex(b *pb.Post) error {
	if _, exists := s.idToDoc[b.GlobalId]; exists {
		log.Printf("WARNING: %d id already exists in index.", b.GlobalId)
		return errors.New("document already exists with that id")
	}

	id := strconv.FormatInt(b.GlobalId, 10)
	err := s.index.Index(id, b)
	if err != nil {
		return err
	}
	s.idToDoc[b.GlobalId] = b

	return nil
}

func (s *Server) initIndex() {
	req := &pb.PostsRequest{
		RequestType: pb.PostsRequest_FIND,
	}

	ctx := context.Background()
	res, err := s.db.Posts(ctx, req)
	if err != nil {
		log.Fatalf("Failed to create index: %v", err)
	}

	results := util.ConvertDBToFeed(ctx, res, s.db)

	for _, blog := range results {
		if err := s.addToIndex(blog); err != nil {
			log.Fatalf("initIndex: cannot add blog (id %b) to index: %v",
				blog.GlobalId, err)
		}
	}

	log.Printf("Built index of length %d", len(res.Results))
}

func (s *Server) Search(ctx context.Context, r *pb.SearchRequest) (*pb.SearchResponse, error) {
	const (
		MAX_RESULTS = 50
	)

	q := bleve.NewMatchQuery(r.Query.QueryText)
	search := bleve.NewSearchRequest(q)
	search.Size = MAX_RESULTS
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
			continue
		}

		resp.Results = append(resp.Results, doc)
	}
	return resp, nil
}

func (s *Server) Index(ctx context.Context, r *pb.IndexRequest) (*pb.IndexResponse, error) {
	const (
		convErr = "util.ConvertDBToFeed: couldn't convert PostsEntry to Post type: bad results"
	)

	p := util.ConvertDBToFeed(ctx, &pb.PostsResponse{Results: []*pb.PostsEntry{r.Post}}, s.db)
	if len(p) != 1 {
		log.Print(convErr)
		return nil, errors.New(convErr)
	}

	if err := s.addToIndex(p[0]); err != nil {
		log.Printf("Error adding to index: ", err.Error())
		return &pb.IndexResponse{
			ResultType: pb.IndexResponse_ERROR,
			Error:      err.Error(),
		}, nil
	}

	log.Printf("Indexed article with id %d", p[0].GlobalId)
	return &pb.IndexResponse{}, nil
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
