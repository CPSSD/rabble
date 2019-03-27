package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/golang/protobuf/ptypes"
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
			Rss: "unused",
		},
	}
	findResp, findErr := s.db.Users(ctx, urFind)
	if findErr != nil {
		return nil, fmt.Errorf(allRssUserErrorFmt, findErr)
	}
	if findResp.ResultType != pb.UsersResponse_OK {
		return nil, fmt.Errorf(allRssUserErrorFmt, findResp.Error)
	}
	if len(findResp.Results) < 1 {
		return nil, fmt.Errorf("No RSS users in db\n")
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
		content := r.Content
		if content == "" {
			content = r.Description
		}
		postArray = append(postArray, &pb.PostsEntry{
			AuthorId:         authorId,
			Title:            r.Title,
			Body:             content,
			CreationDatetime: creationTime,
		})
	}
	return postArray
}

func (s *serverWrapper) runScraper() {
	ctx, cancel := context.WithTimeout(context.Background(), scraperInterval-time.Minute)
	defer cancel()
	// get all rss users from db
	users, findErr := s.getAllRssUsers(ctx)
	if findErr != nil {
		log.Printf("Scraper all users find got: %v\n", findErr.Error())
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
			postFormArray := s.convertFeedToPost(feed, u.GlobalId)
			// Get all the rss feed user's posts
			posts, postFindErr := s.GetUserPosts(ctx, u.GlobalId)
			if postFindErr != nil {
				log.Printf("Scraper post find got: %v\n", findErr.Error())
				return
			}

			// TODO (sailslick) if posts have been updated update
			// note latest timestamp of these Posts
			latestTimestamp, _ := ptypes.TimestampProto(time.Unix(0, 0))
			for _, post := range posts {
				if latestTimestamp.GetSeconds() < post.CreationDatetime.GetSeconds() {
					latestTimestamp = post.CreationDatetime
				}
			}
			// use the latest timestamp from last to get all new posts
			for _, p := range postFormArray {
				if latestTimestamp.GetSeconds() < p.CreationDatetime.GetSeconds() {
					log.Printf("Making new article, title: %s\n", p.Title)
					s.sendCreateArticle(ctx, u.GlobalId, p.Title, p.Body, p.CreationDatetime)
				}
			}

			<-guard
			wg.Done()
		}(user)
	}

	wg.Wait()
}
