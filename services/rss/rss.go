package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"sync"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/mmcdole/gofeed"
	"google.golang.org/grpc"
)

const (
	scraperInterval = time.Minute * 1
	goRoutineCount = 10
)

type serverWrapper struct {
	dbConn     *grpc.ClientConn
	db         pb.DatabaseClient
	feedParser *gofeed.Parser
	server     *grpc.Server
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

	log.Println(feed.Title)

	rssr.ResultType = pb.NewRssFeedResponse_ACCEPTED

	return rssr, nil
}

func (s *serverWrapper) runScraper() {
	// TODO (sailslick) get all rss users from db instead of steady list
	rssUrls := []string{"http://news.ycombinator.com/rss", "https://www.rte.ie/news/rss/news-headlines.xml"}

	guard := make(chan struct{}, goRoutineCount)
	var wg sync.WaitGroup

	for _, url := range rssUrls {
		guard <- struct{}{}
		wg.Add(1)
		go func(u string) {
			feed, rssGetErr := s.GetRssFeed(u)

			if rssGetErr != nil {
				log.Println(rssGetErr)
				<- guard
				wg.Done()
				return
			}

			// TODO (sailslick) convert feed to user items and update them
			log.Println(feed.Title)

			<- guard
			wg.Done()
		}(url)
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
		log.Fatalf("Skinny server did not connect: %v", err)
	}
	client := pb.NewDatabaseClient(conn)
	return conn, client
}

func buildServerWrapper() *serverWrapper {
	dbConn, dbClient := createDatabaseClient()
	fp := gofeed.NewParser()
	grpcSrv := grpc.NewServer()

	return &serverWrapper {
		dbConn:     dbConn,
		db:         dbClient,
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
			log.Println(serveErr)
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
	os.Exit(0)
}
