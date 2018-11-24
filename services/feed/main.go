package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"google.golang.org/grpc"
)

// convertDBToFeed converts PostsResponses to FeedResponses.
// Hopefully this will removed once we fix proto building.
func (s *server) convertDBToFeed(ctx context.Context, p *pb.PostsResponse) *pb.FeedResponse {
	fp := &pb.FeedResponse{}
	for _, r := range p.Results {
		// TODO(iandioch): Find a way to avoid or cache these requests.
		author, err := s.getAuthorFromDb(ctx, "", "", r.AuthorId)
		if err != nil {
			// Error has already been logged.
			continue
		}
		np := &pb.Post{
			GlobalId: r.GlobalId,
			// TODO(iandioch): Consider what happens for foreign users.
			Author:           author.Handle,
			Title:            r.Title,
			Body:             r.Body,
			CreationDatetime: r.CreationDatetime,
		}
		fp.Results = append(fp.Results, np)
	}
	return fp
}

func (s *server) convertManyToFeed(ctx context.Context, posts []*pb.PostsResponse) *pb.FeedResponse {
	fp := &pb.FeedResponse{}
	for _, p := range posts {
		r := s.convertDBToFeed(ctx, p)
		fp.Results = append(fp.Results, r.Results...)
	}
	return fp
}

func (s *server) getAuthorFromDb(ctx context.Context, handle string, host string, globalId int64) (*pb.UsersEntry, error) {
	const errFmt = "Could not find user %v@%v. error: %v"
	r := &pb.UsersRequest{
		RequestType: pb.UsersRequest_FIND,
		Match: &pb.UsersEntry{
			Handle:   handle,
			Host:     host,
			GlobalId: globalId,
		},
	}

	resp, err := s.db.Users(ctx, r)
	if err != nil {
		return nil, fmt.Errorf(errFmt, handle, host, err)
	}

	if resp.ResultType != pb.UsersResponse_OK {
		return nil, fmt.Errorf(errFmt, handle, host, resp.Error)
	}

	if len(resp.Results) == 0 {
		return nil, fmt.Errorf(errFmt, handle, host, "user does not exist")
	}

	return resp.Results[0], nil
}

type server struct {
	db pb.DatabaseClient
}

func (s *server) getFollows(ctx context.Context, u *pb.UsersEntry) ([]*pb.Follow, error) {
	const errorFmt = "Could not get follows for user %#v: %v"

	r := &pb.DbFollowRequest{
		RequestType: pb.DbFollowRequest_FIND,
		Match:       &pb.Follow{Follower: u.GlobalId},
	}

	ctx, cancel := context.WithTimeout(ctx, time.Second)
	defer cancel()

	resp, err := s.db.Follow(ctx, r)
	if err != nil {
		return nil, fmt.Errorf(errorFmt, *u, err)
	}

	if resp.ResultType != pb.DbFollowResponse_OK {
		return nil, fmt.Errorf(errorFmt, *u, resp.Error)
	}

	return resp.Results, nil
}

// GetUserFeed returns all posts from users that a person is following.
// It is not a service directly, it is called if there is a username in a feed.Get.
func (s *server) GetUserFeed(ctx context.Context, r *pb.FeedRequest) (*pb.FeedResponse, error) {
	const feedErr = "feed.GetUserFeed(%v) failed: %v"

	author, err := s.getAuthorFromDb(ctx, r.Username, "", 0)
	if err != nil {
		err := fmt.Errorf(feedErr, r.Username, err)
		log.Print(err)
		return nil, err
	}

	follows, err := s.getFollows(ctx, author)
	if err != nil {
		err := fmt.Errorf(feedErr, r.Username, err)
		log.Print(err)
		return nil, err
	}

	posts := []*pb.PostsResponse{}
	for _, f := range follows {
		pr := &pb.PostsRequest{
			RequestType: pb.PostsRequest_FIND,
			Match:       &pb.PostsEntry{AuthorId: f.Followed},
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		resp, err := s.db.Posts(ctx, pr)
		if err != nil {
			err := fmt.Errorf(feedErr, r.Username, err)
			log.Print(err)
			return nil, err
		}

		posts = append(posts, resp)
	}

	return s.convertManyToFeed(ctx, posts), nil
}

// Get is responsible for handling feeds
// It takes an optional username argument, if it exists it sends the request to
// GetUserFeed, otherwise it returns all articles on the instance.
func (s *server) Get(ctx context.Context, r *pb.FeedRequest) (*pb.FeedResponse, error) {
	log.Printf("Username: %s\n", r.Username)
	if r.Username != "" {
		return s.GetUserFeed(ctx, r)
	}

	pr := &pb.PostsRequest{
		RequestType: pb.PostsRequest_FIND,
	}

	ctx, cancel := context.WithTimeout(ctx, time.Second)
	defer cancel()

	resp, err := s.db.Posts(ctx, pr)
	if err != nil {
		return nil, fmt.Errorf("feed.Get failed: db.Posts(%v) error: %v", *pr, err)
	}

	return s.convertDBToFeed(ctx, resp), nil
}

func (s *server) PerArticle(ctx context.Context, r *pb.ArticleRequest) (*pb.FeedResponse, error) {
	log.Printf("In per article, ID: %d\n", r.ArticleId)
	pr := &pb.PostsRequest{
		RequestType: pb.PostsRequest_FIND,
		Match: &pb.PostsEntry{
			GlobalId: r.ArticleId,
		},
	}

	resp, err := s.db.Posts(ctx, pr)
	if err != nil {
		log.Print("Single article db get went wrong. Error: %v", err)
		return nil, fmt.Errorf("feed.Get failed: db.Posts(%v) error: %v", *pr, err)
	}

	return s.convertDBToFeed(ctx, resp), nil
}

func (s *server) PerUser(ctx context.Context, r *pb.FeedRequest) (*pb.FeedResponse, error) {
	if r.Username == "" {
		return nil, fmt.Errorf("feed.PerUser failed: username field empty")
	}

	author, err := s.getAuthorFromDb(ctx, r.Username, "", 0)
	if err != nil {
		return nil, err
	}
	authorId := author.GlobalId

	pr := &pb.PostsRequest{
		RequestType: pb.PostsRequest_FIND,
		Match: &pb.PostsEntry{
			AuthorId: authorId,
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	resp, err := s.db.Posts(ctx, pr)
	if err != nil {
		return nil, fmt.Errorf("feed.PerUser failed: db.Posts(%v) error: %v", *pr, err)
	}
	return s.convertDBToFeed(ctx, resp), nil
}

func newServer(c *grpc.ClientConn) *server {
	db := pb.NewDatabaseClient(c)
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
		log.Fatal("DB_SERVICE_HOST env var not set for feed service.")
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
