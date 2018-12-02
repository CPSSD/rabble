package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/mmcdole/gofeed"
)

const (
	scraperInterval    = time.Minute * 15
	goRoutineCount     = 10
	allRssUserErrorFmt = "ERROR: All Rss user find failed. message: %v\n"
)

func (s *serverWrapper) getAllRssUsers(ctx context.Context) ([]*pb.UsersEntry, error) {
	urFind := &pb.UsersRequest{
		RequestType: pb.UsersRequest_FIND_NOT,
		Match: &pb.UsersEntry{
			Rss:    "",
		},
	}
	findResp, findErr := s.db.Users(ctx, urFind)
	if findErr != nil {
		return nil, fmt.Errorf(allRssUserErrorFmt, findErr)
	}
	if findResp.ResultType != pb.UsersResponse_OK || len(findResp.Results) < 1 {
		return nil, fmt.Errorf(allRssUserErrorFmt, findResp.Error)
	}
	return findResp.Results, nil
}

// convertFeedToPost converts gofeed.Feed types to post types.
func (s *serverWrapper) convertFeedToPost(gf *gofeed.Feed, authorId int64) []*pb.PostsEntry {
	postArray := []*pb.PostsEntry{}

	for _, r := range gf.Items {
		// convert time to creation_datetime
		creationTime, creationErr := s.convertFeedItemDatetime(r)
		if creationErr != nil {
			continue
		}

		postArray = append(postArray, &pb.PostsEntry{
			AuthorId:         authorId,
			Title:            r.Title,
			Body:             r.Content,
			CreationDatetime: creationTime,
		})
	}
	return postArray
}

func (s *serverWrapper) runScraper() {
	ctx, cancel := context.WithTimeout(context.Background(), scraperInterval - time.Minute)
	defer cancel()
	// get all rss users from db
	users, findErr := s.getAllRssUsers(ctx)

	if findErr != nil {
		log.Printf(findErr.Error())
	}

	guard := make(chan struct{}, goRoutineCount)
	var wg sync.WaitGroup

	for _, user := range users {
		guard <- struct{}{}
		wg.Add(1)
		go func(u *pb.UsersEntry) {
			feed, rssGetErr := s.GetRssFeed(u.Rss)

			if rssGetErr != nil {
				log.Println(rssGetErr)
				<-guard
				wg.Done()
				return
			}

			// Convert feed to post items
			//postFormArray :=
			s.convertFeedToPost(feed, u.GlobalId)
			log.Println(feed.Title)
			// TODO (sailslick) check if post items are in db/out of date

			// TODO (sailslick) if out of date update

			// TODO (sailslick) if not in db send create article request

			<-guard
			wg.Done()
		}(user)
	}

	wg.Wait()
}
