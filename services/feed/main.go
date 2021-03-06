package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	utils "github.com/cpssd/rabble/services/utils"
	"google.golang.org/grpc"
)

const (
	MaxItemsReturned = 50
)

type server struct {
	db pb.DatabaseClient
}

func (s *server) convertManyToFeed(ctx context.Context, posts []*pb.PostsResponse, shares []*pb.SharesResponse) *pb.FeedResponse {
	fp := &pb.FeedResponse{}
	for _, p := range posts {
		r := utils.ConvertDBToFeed(ctx, p, s.db)
		fp.Results = append(fp.Results, r...)
	}
	for _, shr := range shares {
		r := utils.ConvertShareToFeed(ctx, shr, s.db)
		fp.ShareResults = append(fp.ShareResults, r...)
	}
	return fp
}

func (s *server) getFollows(ctx context.Context, u *pb.UsersEntry) ([]*pb.Follow, error) {
	const errorFmt = "Could not get follows for user %#v: %v"

	r := &pb.DbFollowRequest{
		RequestType: pb.DbFollowRequest_FIND,
		Match:       &pb.Follow{Follower: u.GlobalId},
	}

	ctx, cancel := context.WithTimeout(ctx, time.Second*5)
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

	author, err := utils.GetAuthorFromDb(ctx, "", "", true, r.UserId, s.db)
	if err != nil {
		err := fmt.Errorf(feedErr, r.UserId, err)
		log.Print(err)
		return nil, err
	}

	follows, err := s.getFollows(ctx, author)
	if err != nil {
		err := fmt.Errorf(feedErr, r.UserId, err)
		log.Print(err)
		return nil, err
	}

	posts := []*pb.PostsResponse{}
	shares := []*pb.SharesResponse{}
	for _, f := range follows {
		pr := &pb.PostsRequest{
			RequestType:  pb.PostsRequest_FIND,
			Match:        &pb.PostsEntry{AuthorId: f.Followed},
			UserGlobalId: r.UserGlobalId,
		}

		ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
		defer cancel()

		resp, err := s.db.Posts(ctx, pr)
		if err != nil {
			err := fmt.Errorf(feedErr, r.UserId, err)
			log.Print(err)
			return nil, err
		}
		if resp.ResultType != pb.PostsResponse_OK {
			err := fmt.Errorf(feedErr, r.UserId, resp.Error)
			log.Print(err)
			return nil, err
		}

		posts = append(posts, resp)

		spr := &pb.SharedPostsRequest{
			NumPosts:     MaxItemsReturned,
			SharerId:     f.Followed,
			UserGlobalId: r.UserGlobalId,
		}

		ctx, cancel = context.WithTimeout(context.Background(), time.Second*5)
		defer cancel()

		sharesResp, err := s.db.SharedPosts(ctx, spr)
		if err != nil {
			err := fmt.Errorf(feedErr, r.UserId, err)
			log.Print(err)
			return nil, err
		}
		if sharesResp.ResultType != pb.SharesResponse_OK {
			err := fmt.Errorf(feedErr, r.UserId, sharesResp.Error)
			log.Print(err)
			return nil, err
		}

		shares = append(shares, sharesResp)
	}

	return s.convertManyToFeed(ctx, posts, shares), nil
}

// Get is responsible for handling feeds
// It takes an optional username argument, if it exists it sends the request to
// GetUserFeed, otherwise it returns all articles on the instance.
func (s *server) Get(ctx context.Context, r *pb.FeedRequest) (*pb.FeedResponse, error) {
	log.Printf("UserId: %v.\n", r.UserId)
	if r.UserId != 0 {
		return s.GetUserFeed(ctx, r)
	}

	pr := &pb.InstanceFeedRequest{
		NumPosts:     MaxItemsReturned,
		UserGlobalId: r.UserGlobalId,
	}

	ctx, cancel := context.WithTimeout(ctx, time.Second*5)
	defer cancel()

	resp, err := s.db.InstanceFeed(ctx, pr)
	instanceFeedErrFmt := "feed.Get failed: db.InstanceFeed(%v) error: %v"
	if err != nil {
		return nil, fmt.Errorf(instanceFeedErrFmt, *pr, err)
	}
	if resp.ResultType != pb.PostsResponse_OK {
		return nil, fmt.Errorf(instanceFeedErrFmt, *pr, resp.Error)
	}
	fp := &pb.FeedResponse{}
	fp.Results = utils.ConvertDBToFeed(ctx, resp, s.db)

	return fp, nil
}

func (s *server) PerArticle(ctx context.Context, r *pb.ArticleRequest) (*pb.FeedResponse, error) {
	log.Printf("In per article, ID: %d\n", r.ArticleId)
	pr := &pb.PostsRequest{
		RequestType:  pb.PostsRequest_FIND,
		UserGlobalId: r.UserGlobalId,
		Match: &pb.PostsEntry{
			GlobalId: r.ArticleId,
		},
	}

	resp, err := s.db.Posts(ctx, pr)
	postsErrFmt := "feed.Get failed: db.Posts(%v) error: %v"
	if err != nil {
		log.Printf(postsErrFmt, *pr, err)
		return nil, fmt.Errorf(postsErrFmt, *pr, err)
	}
	if resp.ResultType != pb.PostsResponse_OK {
		log.Printf(postsErrFmt, *pr, resp.Error)
		return nil, fmt.Errorf(postsErrFmt, *pr, resp.Error)
	}

	if len(resp.Results) > 1 {
		log.Print("Single article db get went wrong. Got multiple articles.")
		return nil, errors.New("feed.Get failed: db.Posts(%v) got multiple articles")
	}

	if len(resp.Results) == 0 {
		return &pb.FeedResponse{}, nil
	}

	author, err := utils.GetAuthorFromDb(ctx, "", "", false, resp.Results[0].AuthorId, s.db)
	if err != nil {
		return nil, err
	}

	if author.Private != nil && author.Private.Value {
		if r.UserGlobalId == nil {
			// User not logged in.
			return &pb.FeedResponse{Error: pb.FeedResponse_UNAUTHORIZED}, nil
		}
		following, err := s.checkFollowing(r.UserGlobalId.Value, author.GlobalId)
		if err != nil {
			return nil, err
		} else if !following {
			// User not following this private account.
			return &pb.FeedResponse{Error: pb.FeedResponse_UNAUTHORIZED}, nil
		}
	}
	fp := &pb.FeedResponse{}
	fp.Results = utils.ConvertDBToFeed(ctx, resp, s.db)
	return fp, nil
}

func (s *server) checkFollowing(follower_id int64, followed_id int64) (bool, error) {
	if follower_id == followed_id {
		return true, nil // Users are 'following' themselves.
	}
	fr := &pb.DbFollowRequest{
		RequestType: pb.DbFollowRequest_FIND,
		Match: &pb.Follow{
			Follower: follower_id,
			Followed: followed_id,
			State:    pb.Follow_ACTIVE,
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	resp, err := s.db.Follow(ctx, fr)
	followErrFmt := "Checking follower of private account failed: %v"
	if err != nil {
		return false, fmt.Errorf(followErrFmt, err)
	}
	if resp.ResultType != pb.DbFollowResponse_OK {
		return false, fmt.Errorf(followErrFmt, resp.Error)
	}

	// True if there's a match.
	return len(resp.Results) == 1, nil
}

func (s *server) PerUser(ctx context.Context, r *pb.FeedRequest) (*pb.FeedResponse, error) {
	if r.Username == "" {
		return nil, fmt.Errorf("feed.PerUser failed: Username field empty")
	}

	handle, host, err := utils.ParseUsername(r.Username)
	if err != nil {
		return nil, fmt.Errorf("feed.PerUser failed: %v", err)
	}

	host = utils.NormaliseHost(host)

	hostIsNull := host == ""
	author, err := utils.GetAuthorFromDb(ctx, handle, host, hostIsNull, 0, s.db)
	if err != nil {
		log.Print(err)
		return &pb.FeedResponse{Error: pb.FeedResponse_USER_NOT_FOUND}, nil
	}
	authorID := author.GlobalId

	if author.Private != nil && author.Private.Value {
		if r.UserGlobalId == nil {
			// User not logged in.
			return &pb.FeedResponse{Error: pb.FeedResponse_UNAUTHORIZED}, nil
		}
		following, err := s.checkFollowing(r.UserGlobalId.Value, authorID)
		if err != nil {
			return nil, err
		} else if !following {
			// User not following this private account.
			return &pb.FeedResponse{Error: pb.FeedResponse_UNAUTHORIZED}, nil
		}
	}

	pr := &pb.PostsRequest{
		RequestType:  pb.PostsRequest_FIND,
		UserGlobalId: r.UserGlobalId,
		Match: &pb.PostsEntry{
			AuthorId: authorID,
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()
	resp, err := s.db.Posts(ctx, pr)
	postsErrFmt := "feed.PerUser failed: db.Posts(%v) error: %v"
	if err != nil {
		return nil, fmt.Errorf(postsErrFmt, *pr, err)
	}
	if resp.ResultType != pb.PostsResponse_OK {
		return nil, fmt.Errorf(postsErrFmt, *pr, resp.Error)
	}

	spr := &pb.SharedPostsRequest{
		NumPosts:     MaxItemsReturned,
		SharerId:     authorID,
		UserGlobalId: r.UserGlobalId,
	}

	ctx, cancel = context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()

	shareResp, err := s.db.SharedPosts(ctx, spr)
	shareErrFmt := "feed.PerUser failed: db.SharedPosts(%v) error: %v"
	if err != nil {
		return nil, fmt.Errorf(shareErrFmt, *spr, err)
	}
	if shareResp.ResultType != pb.SharesResponse_OK {
		return nil, fmt.Errorf(shareErrFmt, *spr, shareResp.Error)
	}
	fp := &pb.FeedResponse{}
	fp.Results = utils.ConvertDBToFeed(ctx, resp, s.db)
	fp.ShareResults = utils.ConvertShareToFeed(ctx, shareResp, s.db)
	return fp, nil
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
