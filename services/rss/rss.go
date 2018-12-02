package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/golang/protobuf/ptypes"
	tspb "github.com/golang/protobuf/ptypes/timestamp"
	"github.com/mmcdole/gofeed"
	"google.golang.org/grpc"
)

const (
	scraperInterval    = time.Minute * 15
	goRoutineCount     = 10
	allRssUserErrorFmt = "ERROR: All Rss user find failed. message: %v\n"
)

type Parser interface {
	ParseURL(string) (*gofeed.Feed, error)
}

type serverWrapper struct {
	dbConn     *grpc.ClientConn
	db         pb.DatabaseClient
	artConn    *grpc.ClientConn
	art        pb.ArticleClient
	feedParser Parser
	server     *grpc.Server
}

// convertFeedItemDatetime converts gofeed.Item.Published type to protobud timestamp
func (s *serverWrapper) convertFeedItemDatetime(gi *gofeed.Item) (*tspb.Timestamp, error) {
	parsedTimestamp := *gi.PublishedParsed
	if (parsedTimestamp == time.Time{}) {
		log.Printf("No timestamp for feed: %s\n", gi.Link)
		parsedTimestamp = time.Now()
	}

	protoTimestamp, protoTimeErr := ptypes.TimestampProto(parsedTimestamp)
	if protoTimeErr != nil {
		log.Printf("Error converting timestamp: %s\n", protoTimeErr)
		return nil, fmt.Errorf("Invalid timestamp\n")
	}
	return protoTimestamp, nil
}

func (s *serverWrapper) convertRssUrlToHandle(url string) string {
	// Converts url in form: https://news.ycombinator.com/rss
	// to: news.ycombinator.com-rss
	if strings.HasPrefix(url, "http") {
		url = strings.Split(url, "//")[1]
	}
	return strings.Replace(url, "/", "-", -1)
}

func (s *serverWrapper) sendCreateArticle(ctx context.Context, author string, it *gofeed.Item, cTime *tspb.Timestamp) {
	na := &pb.NewArticle{
		Author:           author,
		Title:            it.Title,
		Body:             it.Content,
		CreationDatetime: cTime,
		Foreign:          false,
	}
	newArtResp, newArtErr := s.art.CreateNewArticle(ctx, na)
	if newArtErr != nil {
		log.Printf("ERROR: Could not create new article: %v", newArtErr)
	} else if newArtResp.ResultType != pb.NewArticleResponse_OK {
		log.Printf("ERROR: Could not create new article message: %v", newArtResp.Error)
	}
}

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

// createArticlesFromFeed converts gofeed.Feed types to article type.
func (s *serverWrapper) createArticlesFromFeed(ctx context.Context, gf *gofeed.Feed, author string) {
	for _, r := range gf.Items {
		// convert time to creation_datetime
		creationTime, creationErr := s.convertFeedItemDatetime(r)
		if creationErr != nil {
			continue
		}
		s.sendCreateArticle(ctx, author, r, creationTime)
	}
}

func (s *serverWrapper) GetRssFeed(url string) (*gofeed.Feed, error) {
	feed, parseErr := s.feedParser.ParseURL(url)

	if parseErr != nil {
		return nil, fmt.Errorf("While getting rss feed `%s` got err: %v", url, parseErr)
	}

	return feed, nil
}

func (s *serverWrapper) NewRssFeedItem(ctx context.Context, r *pb.NewRssArticle) (*pb.RssResponse, error) {
	log.Printf("Got a new article to add to rss with title: %s\n", r.Title)

	rssr := &pb.RssResponse{}
	rssr.ResultType = pb.RssResponse_ACCEPTED

	return rssr, nil
}

func (s *serverWrapper) NewRssFollow(ctx context.Context, r *pb.NewRssFeed) (*pb.NewRssFeedResponse, error) {
	log.Printf("Got a new RSS follow for site: %s\n", r.RssUrl)
	rssr := &pb.NewRssFeedResponse{}

	feed, err := s.GetRssFeed(r.RssUrl)

	if err != nil {
		log.Println(err)
		rssr.ResultType = pb.NewRssFeedResponse_ERROR
		rssr.Message = err.Error()
		return rssr, nil
	}

	handle := s.convertRssUrlToHandle(r.RssUrl)
	// add new user with feed details
	urInsert := &pb.UsersRequest{
		RequestType: pb.UsersRequest_INSERT,
		Entry: &pb.UsersEntry{
			Handle: handle,
			Rss:    r.RssUrl,
		},
	}
	insertResp, insertErr := s.db.Users(ctx, urInsert)

	if insertErr != nil {
		log.Printf("Error on rss user insert: %v\n", insertErr)
		rssr.ResultType = pb.NewRssFeedResponse_ERROR
		rssr.Message = insertErr.Error()
		return rssr, nil
	}

	if insertResp.ResultType != pb.UsersResponse_OK {
		log.Printf("Rss user insert failed. message: %v\n", insertResp.Error)
		rssr.ResultType = pb.NewRssFeedResponse_ERROR
		rssr.Message = insertResp.Error
		return rssr, nil
	}

	// get that new user's globalId
	urFind := &pb.UsersRequest{
		RequestType: pb.UsersRequest_FIND,
		Match: &pb.UsersEntry{
			Handle: handle,
			Rss:    r.RssUrl,
		},
	}
	findResp, findErr := s.db.Users(ctx, urFind)

	if findErr != nil {
		log.Printf("Error on rss user find: %v\n", findErr)
		rssr.ResultType = pb.NewRssFeedResponse_ERROR
		rssr.Message = findErr.Error()
		return rssr, nil
	}

	if findResp.ResultType != pb.UsersResponse_OK || len(findResp.Results) < 1 {
		log.Printf("Rss user find failed. message: %v\n", findResp.Error)
		rssr.ResultType = pb.NewRssFeedResponse_ERROR
		rssr.Message = findResp.Error
		return rssr, nil
	}

	log.Println(feed.Title)
	// convert feed to post items and save
	s.createArticlesFromFeed(ctx, feed, findResp.Results[0].Handle)

	rssr.ResultType = pb.NewRssFeedResponse_ACCEPTED
	rssr.GlobalId = findResp.Results[0].GlobalId

	return rssr, nil
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

func createDatabaseClient() (*grpc.ClientConn, pb.DatabaseClient) {
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

func createArticleClient() (*grpc.ClientConn, pb.ArticleClient) {
	host := os.Getenv("ARTICLE_SERVICE_HOST")
	if host == "" {
		log.Fatal("ARTICLE_SERVICE_HOST env var not set for rss service.")
	}
	addr := host + ":1601"

	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Rss server did not connect to article service: %v", err)
	}
	client := pb.NewArticleClient(conn)
	return conn, client
}

func buildServerWrapper() *serverWrapper {
	dbConn, dbClient := createDatabaseClient()
	artConn, artClient := createArticleClient()
	fp := gofeed.NewParser()
	grpcSrv := grpc.NewServer()

	return &serverWrapper{
		dbConn:     dbConn,
		db:         dbClient,
		artConn:    artConn,
		art:        artClient,
		feedParser: fp,
		server:     grpcSrv,
	}
}

func main() {
	log.Print("Starting rss on port: 1973")
	lis, netErr := net.Listen("tcp", ":1973")
	if netErr != nil {
		log.Fatalf("failed to listen: %v", netErr)
	}

	serverWrapper := buildServerWrapper()
	pb.RegisterRSSServer(serverWrapper.server, serverWrapper)

	go func() {
		if serveErr := serverWrapper.server.Serve(lis); serveErr != nil {
			log.Fatalf("failed to serve: %v", serveErr)
		}
	}()

	scraperTicker := time.NewTicker(scraperInterval)

	for t := range scraperTicker.C {
		log.Print("Starting rss on port: 1973, time: ", t.String())
		serverWrapper.runScraper()
	}

	// Accept graceful shutdowns when quit via SIGINT or SIGTERM. Other signals
	// (eg. SIGKILL, SIGQUIT) will not be caught.
	// Docker sends a SIGTERM on shutdown.
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)

	// Block until we receive signal.
	<-c
	scraperTicker.Stop()
	serverWrapper.server.Stop()
	serverWrapper.dbConn.Close()
	serverWrapper.artConn.Close()
	os.Exit(0)
}
