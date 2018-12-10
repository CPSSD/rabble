package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/golang/protobuf/ptypes"
	tspb "github.com/golang/protobuf/ptypes/timestamp"
	"github.com/mmcdole/gofeed"
	"google.golang.org/grpc"
)

const (
	findUserErrorFmt      = "ERROR: User(%v) find failed. message: %v\n"
	findUserPostsErrorFmt = "ERROR: User id(%v) posts find failed. message: %v\n"
	rssTimeParseFormat    = "Mon, 02 Jan 2006 15:04:05 -0700"
	rssDeclare            = `<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel>`
	rssDeclareEnd         = `</channel></rss>`
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
	hostname   string
}

// convertFeedItemDatetime converts gofeed.Item.Published type to protobuf timestamp
func (s *serverWrapper) convertFeedItemDatetime(gi *gofeed.Item) (*tspb.Timestamp, error) {
	parsedTimestamp := time.Now()
	if (gi.PublishedParsed != &time.Time{} && gi.PublishedParsed != nil) {
		log.Printf("No timestamp for feed: %s\n", gi.Link)
		parsedTimestamp = *gi.PublishedParsed
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

func (s *serverWrapper) sendCreateArticle(ctx context.Context, author string, title string, content string, cTime *tspb.Timestamp) {
	na := &pb.NewArticle{
		Author:           author,
		Title:            title,
		Body:             content,
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

// createArticlesFromFeed converts gofeed.Feed types to article type.
func (s *serverWrapper) createArticlesFromFeed(ctx context.Context, gf *gofeed.Feed, author string) {
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
		s.sendCreateArticle(ctx, author, r.Title, content, creationTime)
	}
}

func (s *serverWrapper) createRssHeader(ue *pb.UsersEntry) string {
	link := s.hostname + "/c2s/@" + ue.Handle
	datetime := time.Now().Format(rssTimeParseFormat)
	return "<title>Rabble blog for " + ue.Handle + "</title>\n" +
		"<description>" + ue.Bio + "</description>\n" +
		"<link>" + link + "</link>\n" +
		"<pubDate>" + datetime + "</pubDate>\n"
}

func (s *serverWrapper) createRssItem(ue *pb.UsersEntry, pe *pb.PostsEntry) string {
	link := s.hostname + "/c2s/@" + ue.Handle + "/" + strconv.FormatInt(pe.GlobalId, 10)
	timestamp, _ := ptypes.Timestamp(pe.CreationDatetime)
	datetime := timestamp.Format(rssTimeParseFormat)
	return "<item>\n" +
		"<title>" + pe.Title + "</title>\n" +
		"<link>" + link + "</link>\n" +
		"<description>" + pe.MdBody + "</description>\n" +
		"<pubDate>" + datetime + "</pubDate>\n" +
		"</item>\n"

}

func (s *serverWrapper) GetUser(ctx context.Context, handle string) (*pb.UsersEntry, error) {
	urFind := &pb.UsersRequest{
		RequestType: pb.UsersRequest_FIND,
		Match: &pb.UsersEntry{
			Handle: handle,
		},
	}
	findResp, findErr := s.db.Users(ctx, urFind)
	if findErr != nil {
		return nil, fmt.Errorf(findUserErrorFmt, handle, findErr)
	}
	if findResp.ResultType != pb.UsersResponse_OK {
		return nil, fmt.Errorf(findUserErrorFmt, handle, findResp.Error)
	}
	if len(findResp.Results) < 1 {
		return nil, fmt.Errorf("No users in db in handle: %v\n", handle)
	}
	if len(findResp.Results) > 1 {
		return nil, fmt.Errorf("Multiple users with handle: %v in db\n", handle)
	}
	return findResp.Results[0], nil
}

func (s *serverWrapper) GetUserPosts(ctx context.Context, authorId int64) ([]*pb.PostsEntry, error) {
	findReq := &pb.PostsRequest{
		RequestType: pb.PostsRequest_FIND,
		Match: &pb.PostsEntry{
			AuthorId: authorId,
		},
	}
	findResp, findErr := s.db.Posts(ctx, findReq)
	if findErr != nil {
		return nil, fmt.Errorf(findUserPostsErrorFmt, authorId, findErr)
	}
	if findResp.ResultType != pb.PostsResponse_OK {
		return nil, fmt.Errorf(findUserPostsErrorFmt, authorId, findResp.Error)
	}
	return findResp.Results, nil
}

func (s *serverWrapper) GetRssFeed(url string) (*gofeed.Feed, error) {
	feed, parseErr := s.feedParser.ParseURL(url)

	if parseErr != nil {
		return nil, fmt.Errorf("While getting rss feed `%s` got err: %v", url, parseErr)
	}

	return feed, nil
}

func (s *serverWrapper) PerUserRss(ctx context.Context, r *pb.UsersEntry) (*pb.RssResponse, error) {
	log.Printf("Got a per user request for user: %s\n", r.Handle)
	rssr := &pb.RssResponse{}

	// Get user details
	ue, userErr := s.GetUser(ctx, r.Handle)
	if userErr != nil {
		log.Printf("PerUserRss user find got: %v\n", userErr.Error())
		rssr.ResultType = pb.RssResponse_ERROR
		rssr.Message = userErr.Error()
		return rssr, nil
	}

	if ue.Private {
		log.Printf("%s is a private user.\n", r.Handle)
		rssr.ResultType = pb.RssResponse_ERROR
		rssr.Message = "Can not create RSS feed for private user."
		return rssr, nil
	}

	// Get user posts
	posts, postFindErr := s.GetUserPosts(ctx, ue.GlobalId)
	if postFindErr != nil {
		log.Printf("PerUserRss posts find got: %v\n", postFindErr.Error())
		rssr.ResultType = pb.RssResponse_ERROR
		rssr.Message = postFindErr.Error()
		return rssr, nil
	}

	// Construct rss header
	rssHeader := s.createRssHeader(ue)
	rssFeed := rssDeclare + rssHeader

	// Take most recent 10 posts
	sort.SliceStable(posts, func(i int, j int) bool {
		return posts[i].CreationDatetime.GetSeconds() < posts[j].CreationDatetime.GetSeconds()
	})
	n := 10
	if len(posts) < 10 {
		n = len(posts)
	}
	topTen := posts[:n]

	// Convert each post to rss entry
	for _, post := range topTen {
		// Add all rss entrys into body
		rssFeed += s.createRssItem(ue, post)
	}

	rssFeed += rssDeclareEnd
	rssr.ResultType = pb.RssResponse_ACCEPTED
	rssr.Feed = rssFeed

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
	hostname := os.Getenv("HOST_NAME")
	if hostname == "" {
		log.Fatal("HOST_NAME env var not set for rss service.")
	}

	return &serverWrapper{
		dbConn:     dbConn,
		db:         dbClient,
		artConn:    artConn,
		art:        artClient,
		feedParser: fp,
		server:     grpcSrv,
		hostname:   hostname,
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
		log.Print("Starting scraper, time: ", t.String())
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
