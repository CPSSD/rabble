package util

import (
	"context"
	"fmt"
	"log"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/golang/protobuf/ptypes"
	tspb "github.com/golang/protobuf/ptypes/timestamp"
	"google.golang.org/grpc"
)

const (
	defaultImage     = "https://qph.fs.quoracdn.net/main-qimg-8aff684700be1b8c47fa370b6ad9ca13.webp"
	MaxItemsReturned = 50
	timeParseFormat  = "2006-01-02T15:04:05.000Z"
)

// ConvertPbTimestamp converts a timestamp into a format readable by the frontend
func ConvertPbTimestamp(t *tspb.Timestamp) string {
	goTime, err := ptypes.Timestamp(t)
	if err != nil {
		log.Print(err)
		return time.Now().Format(timeParseFormat)
	}
	return goTime.Format(timeParseFormat)
}

type UsersGetter interface {
	Users(ctx context.Context, in *pb.UsersRequest, opts ...grpc.CallOption) (*pb.UsersResponse, error)
}

func GetAuthorFromDb(ctx context.Context, handle string, host string, globalId int64, db UsersGetter) (*pb.UsersEntry, error) {
	const errFmt = "Could not find user %v@%v. error: %v"
	r := &pb.UsersRequest{
		RequestType: pb.UsersRequest_FIND,
		Match: &pb.UsersEntry{
			Handle:   handle,
			Host:     host,
			GlobalId: globalId,
		},
	}

	resp, err := db.Users(ctx, r)
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

// convertDBToFeed converts PostsResponses to PostsEntry[]
// Hopefully this will removed once we fix proto building.
func ConvertDBToFeed(ctx context.Context, p *pb.PostsResponse, db UsersGetter) []*pb.Post {
	pe := []*pb.Post{}
	for i, r := range p.Results {
		if i >= MaxItemsReturned {
			// Have hit limit for number of items returned for this request.
			break
		}

		// TODO(iandioch): Find a way to avoid or cache these requests.
		author, err := GetAuthorFromDb(ctx, "", "", r.AuthorId, db)
		if err != nil {
			log.Println(err)
			continue
		}
		np := &pb.Post{
			GlobalId: r.GlobalId,
			// TODO(iandioch): Consider what happens for foreign users.
			Author:     author.Handle,
			Title:      r.Title,
			Bio:        author.Bio,
			Body:       r.Body,
			Image:      defaultImage,
			LikesCount: r.LikesCount,
			IsLiked:    r.IsLiked,
			Published:  ConvertPbTimestamp(r.CreationDatetime),
            IsFollowed: r.IsFollowed,
		}
		pe = append(pe, np)
	}
	return pe
}

// ConvertDBToUsers converts database.UserResponses to search.Users[]
func ConvertDBToUsers(ctx context.Context, p *pb.UsersResponse, db UsersGetter) []*pb.User {
	ue := []*pb.User{}
	for i, r := range p.Results {
		if i >= MaxItemsReturned {
			// Have hit limit for number of items returned for this request.
			break
		}
		np := &pb.User{
			GlobalId: r.GlobalId,
			Handle:   r.Handle,
			Bio:      r.Bio,
			Host:     r.Host,
		}
		ue = append(ue, np)
	}
	return ue
}
