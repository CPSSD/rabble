package main

import (
	"context"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	pb "github.com/cpssd/rabble/services/proto"
	//"github.com/mmcdole/gofeed"
	"google.golang.org/grpc"
)

type serverWrapper struct {
	dbConn *grpc.ClientConn
	db     pb.DatabaseClient
	server *grpc.Server
}

func (s *serverWrapper) NewRssFeedItem(ctx context.Context, r *pb.NewRssArticle) (*pb.RssResponse, error) {
	log.Printf("Got a new article to add to rss with title: %s\n", r.Title)

	rssr := &pb.RssResponse{}

	rssr.ResultType = pb.RssResponse_ACCEPTED

	return rssr, nil
}

func (s *serverWrapper) NewRssFollow(ctx context.Context, r *pb.NewRssFeed) (*pb.RssResponse, error) {
	log.Printf("Got a new RSS follow for site: %s\n", r.RssUri)

	rssr := &pb.RssResponse{}

	rssr.ResultType = pb.RssResponse_ACCEPTED

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
		log.Fatalf("Skinny server did not connect: %v", err)
	}
	client := pb.NewDatabaseClient(conn)
	return conn, client
}

func buildServerWrapper() *serverWrapper {
	dbConn, dbClient := createDatabaseClient()
	grpcSrv := grpc.NewServer()

	return &serverWrapper {
		dbConn: dbConn,
		db:     dbClient,
		server: grpcSrv,
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

	// Accept graceful shutdowns when quit via SIGINT or SIGTERM. Other signals
	// (eg. SIGKILL, SIGQUIT) will not be caught.
	// Docker sends a SIGTERM on shutdown.
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)

	// Block until we receive signal.
	<-c
	serverWrapper.server.Stop()
	serverWrapper.dbConn.Close()
	os.Exit(0)
}
