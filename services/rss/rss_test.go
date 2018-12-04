package main

import (
	"context"
	"testing"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/golang/protobuf/ptypes"
	tspb "github.com/golang/protobuf/ptypes/timestamp"
	"github.com/mmcdole/gofeed"
	"google.golang.org/grpc"
)

const (
	fakeTitle   = "fake test title"
	fakeContent = "fake test content"
)

type gofeedFake struct {
	gofeed.Parser
}

func (d *gofeedFake) ParseURL(url string) (*gofeed.Feed, error) {
	return &gofeed.Feed{
		Title: fakeTitle,
	}, nil
}

type ArticleFake struct {
	pb.ArticleClient

	// The most recent NewArticle
	na *pb.NewArticle
}

func (a *ArticleFake) CreateNewArticle(_ context.Context, r *pb.NewArticle, _ ...grpc.CallOption) (*pb.NewArticleResponse, error) {
	a.na = r
	return &pb.NewArticleResponse{
		ResultType: pb.NewArticleResponse_OK,
		GlobalId:   "test id",
	}, nil
}

type DatabaseFake struct {
	pb.DatabaseClient

	ur *pb.UsersRequest
}

func (d *DatabaseFake) Users(_ context.Context, r *pb.UsersRequest, _ ...grpc.CallOption) (*pb.UsersResponse, error) {
	d.ur = r
	ue := &pb.UsersEntry{
		Handle:   "test/rss",
		GlobalId: 1,
		Rss:      "https://news.ycombinator.com/rss",
	}
	return &pb.UsersResponse{
		ResultType: pb.UsersResponse_OK,
		Results:    []*pb.UsersEntry{ue},
	}, nil
}

func newTestServerWrapper() *serverWrapper {
	// TODO(iandioch): Fake/mock instead of using real dependencies

	sw := &serverWrapper{
		server:     &grpc.Server{},
		art:        &ArticleFake{},
		db:         &DatabaseFake{},
		feedParser: &gofeedFake{},
	}
	return sw
}

func TestConvertFeedItemDatetime(t *testing.T) {
	nowProto, _ := ptypes.TimestampProto(time.Now())
	then := time.Unix(0, 0)
	thenProto, _ := ptypes.TimestampProto(then)
	tests := []struct {
		in   *gofeed.Item
		want *tspb.Timestamp
	}{
		{
			in: &gofeed.Item{
				PublishedParsed: &then,
			},
			want: thenProto,
		},
		{
			in:   &gofeed.Item{},
			want: nowProto,
		},
	}

	sw := newTestServerWrapper()
	for _, tcase := range tests {
		convertedTime, _ := sw.convertFeedItemDatetime(tcase.in)
		if convertedTime.GetSeconds() != tcase.want.GetSeconds() {
			t.Fatalf("convertFeedItemDatetime(%v), wanted: %v, got: %v",
				tcase.in, tcase.want, convertedTime)
		}
	}
}

func TestConvertRssUrlToHandle(t *testing.T) {
	tests := []struct {
		in   string
		want string
	}{
		{
			in:   "https://news.ycombinator.com/rss",
			want: "news.ycombinator.com-rss",
		},
		{
			in:   "http://news.ycombinator.com/rss",
			want: "news.ycombinator.com-rss",
		},
		{
			in:   "news.ycombinator.com/rss",
			want: "news.ycombinator.com-rss",
		},
		{
			in:   "http://news.ycombinator.com/tech/rss",
			want: "news.ycombinator.com-tech-rss",
		},
	}

	sw := newTestServerWrapper()
	for _, tcase := range tests {
		convertedHandle := sw.convertRssUrlToHandle(tcase.in)
		if convertedHandle != tcase.want {
			t.Fatalf("convertRssUrlToHandle(%v), wanted: %v, got: %v",
				tcase.in, tcase.want, convertedHandle)
		}
	}
}

func TestNewRssFollow(t *testing.T) {
	sw := newTestServerWrapper()

	req := &pb.NewRssFeed{
		RssUrl: "https://news.ycombinator.com/rss",
	}

	r, err := sw.NewRssFollow(context.Background(), req)
	if err != nil {
		t.Fatalf("NewRssFollow(%v), unexpected error: %v", req.RssUrl, err)
	}

	if r.ResultType != pb.NewRssFeedResponse_ACCEPTED {
		t.Fatalf("NewRssFollow(%v), received non accept result_type: %v", req.RssUrl, r.ResultType)
	}
}

func TestGetAllRssUsers(t *testing.T) {
	sw := newTestServerWrapper()

	users, err := sw.getAllRssUsers(context.Background())
	if err != nil {
		t.Fatalf("getAllRssUsers(), unexpected error: %v", err)
	}

	if len(users) != 1 {
		t.Fatalf("getAllRssUsers(), did not recieve a user from db fake: %v")
	}
}

func TestConvertFeedToPost(t *testing.T) {
	then := time.Unix(0, 0)
	thenProto, _ := ptypes.TimestampProto(then)
	tests := []struct {
		inF   *gofeed.Feed
		inAId int64
		want  []*pb.PostsEntry
	}{
		{
			inF: &gofeed.Feed{
				Items: []*gofeed.Item{
					&gofeed.Item{
						PublishedParsed: &then,
						Title:           fakeTitle,
						Content:         fakeContent,
					},
					&gofeed.Item{
						PublishedParsed: &then,
						Title:           fakeTitle,
						Content:         fakeContent,
					},
				},
			},
			inAId: 2,
			want: []*pb.PostsEntry{
				&pb.PostsEntry{
					AuthorId:         2,
					Title:            fakeTitle,
					Body:             fakeContent,
					CreationDatetime: thenProto,
				},
				&pb.PostsEntry{},
			},
		},
		{
			inF: &gofeed.Feed{
				Items: []*gofeed.Item{
					&gofeed.Item{
						PublishedParsed: &then,
						Title:           fakeTitle,
						Description:     fakeContent,
					},
					&gofeed.Item{
						PublishedParsed: &then,
						Title:           fakeTitle,
						Content:         fakeContent,
					},
				},
			},
			inAId: 2,
			want: []*pb.PostsEntry{
				&pb.PostsEntry{
					AuthorId:         2,
					Title:            fakeTitle,
					Body:             fakeContent,
					CreationDatetime: thenProto,
				},
				&pb.PostsEntry{},
			},
		},
	}

	sw := newTestServerWrapper()
	for _, tcase := range tests {
		convertedPosts := sw.convertFeedToPost(tcase.inF, tcase.inAId)
		if len(convertedPosts) != len(tcase.want) && convertedPosts[0].AuthorId == tcase.want[0].AuthorId {
			t.Fatalf("convertFeedToPost(%v, %v), wanted: %v, got: %v",
				tcase.inF, tcase.inAId, tcase.want, convertedPosts)
		}
	}
}
