package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	"github.com/gorilla/mux"
	"github.com/gorilla/sessions"
	"google.golang.org/grpc"
)

// serverWrapper encapsulates the dependencies and config values of the server
// into one struct. Server endpoint handlers hang off of this struct and can
// access their dependencies through it. See
// https://medium.com/statuscode/how-i-write-go-http-services-after-seven-years-37c208122831
// for rationale and further explanation.
type serverWrapper struct {
	router *mux.Router
	server *http.Server
	store  *sessions.CookieStore

	// The hostname for this skinny instance.
	hostname string

	// actorInboxRouter is responsible for routing activitypub requests
	// based on the Type json parameter
	actorInboxRouter map[string]http.HandlerFunc

	// This map is responsible for correctly routing Undo activities
	// to the function handling the undoing of that particular object.
	undoActivityRouter map[string]http.HandlerFunc

	// shutdownWait specifies how long the server should wait when shutting
	// down for existing connections to finish before forcing a shutdown.
	shutdownWait time.Duration

	// databaseConn is the underlying connection to the Database
	// service. This reference must be retained so it can by closed later.
	databaseConn *grpc.ClientConn
	// database is the RPC client for talking to the database service.
	database pb.DatabaseClient

	followsConn               *grpc.ClientConn
	follows                   pb.FollowsClient
	articleConn               *grpc.ClientConn
	article                   pb.ArticleClient
	feedConn                  *grpc.ClientConn
	feed                      pb.FeedClient
	createConn                *grpc.ClientConn
	create                    pb.CreateClient
	usersConn                 *grpc.ClientConn
	users                     pb.UsersClient
	s2sUndoConn               *grpc.ClientConn
	s2sUndo                   pb.S2SUndoClient
	s2sFollowConn             *grpc.ClientConn
	s2sFollow                 pb.S2SFollowClient
	s2sLikeConn               *grpc.ClientConn
	s2sLike                   pb.S2SLikeClient
	s2sUpdateConn             *grpc.ClientConn
	s2sUpdate                 pb.S2SUpdateClient
	announceConn              *grpc.ClientConn
	announce                  pb.AnnounceClient
	approverConn              *grpc.ClientConn
	approver                  pb.ApproverClient
	rssConn                   *grpc.ClientConn
	rss                       pb.RSSClient
	followRecommendationsConn *grpc.ClientConn
	followRecommendations     pb.FollowRecommendationsClient
	ldNormConn                *grpc.ClientConn
	ldNorm                    pb.LDNormClient
	actorsConn                *grpc.ClientConn
	actors                    pb.ActorsClient
	searchConn                *grpc.ClientConn
	search                    pb.SearchClient
	postRecommendationsConn   *grpc.ClientConn
	postRecommendations       pb.PostRecommendationsClient
}

func (s *serverWrapper) shutdown() {
	log.Printf("Stopping skinny server.\n")
	ctx, cancel := context.WithTimeout(context.Background(), s.shutdownWait)
	defer cancel()
	// Waits for active connections to terminate, or until it hits the timeout.
	s.server.Shutdown(ctx)

	s.databaseConn.Close()
	s.articleConn.Close()
	s.followsConn.Close()
	s.createConn.Close()
	s.feedConn.Close()
	s.usersConn.Close()
	s.s2sUndoConn.Close()
	s.s2sUpdateConn.Close()
	s.s2sFollowConn.Close()
	s.s2sLikeConn.Close()
	s.rssConn.Close()
	s.actorsConn.Close()
	s.searchConn.Close()
	s.announceConn.Close()
	s.postRecommendationsConn.Close()
	s.followRecommendationsConn.Close()
	s.ldNormConn.Close()
	s.approverConn.Close()
}

func grpcConn(env string, port string) *grpc.ClientConn {
	host := os.Getenv(env)
	if host == "" {
		log.Fatalf("%s env var not set for skinny server.", env)
	}
	addr := host + ":" + port
	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Skinny server did not connect to %s: %v", addr, err)
	}
	return conn
}

func createArticleClient() (*grpc.ClientConn, pb.ArticleClient) {
	conn := grpcConn("ARTICLE_SERVICE_HOST", "1601")
	return conn, pb.NewArticleClient(conn)
}

func createCreateClient() (*grpc.ClientConn, pb.CreateClient) {
	conn := grpcConn("CREATE_SERVICE_HOST", "1922")
	return conn, pb.NewCreateClient(conn)
}

func createUsersClient() (*grpc.ClientConn, pb.UsersClient) {
	conn := grpcConn("USERS_SERVICE_HOST", "1534")
	return conn, pb.NewUsersClient(conn)
}

func createDatabaseClient() (*grpc.ClientConn, pb.DatabaseClient) {
	conn := grpcConn("DB_SERVICE_HOST", "1798")
	return conn, pb.NewDatabaseClient(conn)
}

func createFollowsClient() (*grpc.ClientConn, pb.FollowsClient) {
	conn := grpcConn("FOLLOWS_SERVICE_HOST", "1641")
	return conn, pb.NewFollowsClient(conn)
}

func createFeedClient() (*grpc.ClientConn, pb.FeedClient) {
	conn := grpcConn("FEED_SERVICE_HOST", "2012")
	return conn, pb.NewFeedClient(conn)
}

func createS2SFollowClient() (*grpc.ClientConn, pb.S2SFollowClient) {
	conn := grpcConn("FOLLOW_ACTIVITY_SERVICE_HOST", "1922")
	return conn, pb.NewS2SFollowClient(conn)
}

func createApproverClient() (*grpc.ClientConn, pb.ApproverClient) {
	conn := grpcConn("APPROVER_SERVICE_HOST", "2077")
	return conn, pb.NewApproverClient(conn)
}

func createS2SLikeClient() (*grpc.ClientConn, pb.S2SLikeClient) {
	conn := grpcConn("LIKE_SERVICE_HOST", "1848")
	return conn, pb.NewS2SLikeClient(conn)
}

func createS2SUndoClient() (*grpc.ClientConn, pb.S2SUndoClient) {
	conn := grpcConn("UNDO_SERVICE_HOST", "1608")
	return conn, pb.NewS2SUndoClient(conn)
}

func createS2SUpdateClient() (*grpc.ClientConn, pb.S2SUpdateClient) {
	conn := grpcConn("UPDATE_SERVICE_HOST", "2029")
	return conn, pb.NewS2SUpdateClient(conn)
}

func createRSSClient() (*grpc.ClientConn, pb.RSSClient) {
	conn := grpcConn("RSS_SERVICE_HOST", "1973")
	return conn, pb.NewRSSClient(conn)
}

func createFollowRecommendationsClient() (*grpc.ClientConn, pb.FollowRecommendationsClient) {
	conn := grpcConn("FOLLOW_RECOMMENDATIONS_HOST", "1973")
	return conn, pb.NewFollowRecommendationsClient(conn)
}

func createLDNormClient() (*grpc.ClientConn, pb.LDNormClient) {
	conn := grpcConn("LDNORM_SERVICE_HOST", "1804")
	return conn, pb.NewLDNormClient(conn)
}

func createActorsClient() (*grpc.ClientConn, pb.ActorsClient) {
	conn := grpcConn("ACTORS_SERVICE_HOST", "1973")
	return conn, pb.NewActorsClient(conn)
}

func createSearchClient() (*grpc.ClientConn, pb.SearchClient) {
	conn := grpcConn("SEARCH_SERVICE_HOST", "1886")
	return conn, pb.NewSearchClient(conn)
}

func createAnnounceClient() (*grpc.ClientConn, pb.AnnounceClient) {
	conn := grpcConn("ANNOUNCE_SERVICE_HOST", "1919")
	return conn, pb.NewAnnounceClient(conn)
}

func createPostRecommendationsClient() (*grpc.ClientConn, pb.PostRecommendationsClient) {
	conn := grpcConn("POST_RECOMMENDATIONS_SERVICE_HOST", "1814")
	return conn, pb.NewPostRecommendationsClient(conn)
}

// buildServerWrapper sets up all necessary individual parts of the server
// wrapper, and returns one that is ready to run.
func buildServerWrapper() *serverWrapper {
	r := mux.NewRouter()
	host_env := "HOST_NAME"
	hostname := os.Getenv(host_env)
	if hostname == "" {
		log.Fatalf("%s env var not set for skinny server", host_env)
	}
	port_env := "SKINNY_SERVER_PORT"
	port := os.Getenv(port_env)
	if port == "" {
		log.Fatalf("%s env var not set for skinny server", port_env)
	}
	addr := "0.0.0.0:" + port
	srv := &http.Server{
		Addr: addr,
		// Important to specify timeouts in order to prevent Slowloris attacks.
		WriteTimeout: time.Second * 15,
		ReadTimeout:  time.Second * 15,
		IdleTimeout:  time.Second * 60,
		Handler:      r,
	}
	cookie_store := sessions.NewCookieStore([]byte("rabble_key"))
	databaseConn, databaseClient := createDatabaseClient()
	followsConn, followsClient := createFollowsClient()
	articleConn, articleClient := createArticleClient()
	feedConn, feedClient := createFeedClient()
	createConn, createClient := createCreateClient()
	usersConn, usersClient := createUsersClient()
	rssConn, rssClient := createRSSClient()
	ldNormConn, ldNormClient := createLDNormClient()
	s2sUndoConn, s2sUndoClient := createS2SUndoClient()
	s2sUpdateConn, s2sUpdateClient := createS2SUpdateClient()
	s2sFollowConn, s2sFollowClient := createS2SFollowClient()
	s2sLikeConn, s2sLikeClient := createS2SLikeClient()
	approverConn, approverClient := createApproverClient()
	followRecommendationsConn, followRecommendationsClient :=
		createFollowRecommendationsClient()
	actorsConn, actorsClient := createActorsClient()
	searchConn, searchClient := createSearchClient()
	announceConn, announceClient := createAnnounceClient()
	postRecommendationsConn, postRecommendationsClient := createPostRecommendationsClient()
	s := &serverWrapper{
		router:                    r,
		server:                    srv,
		store:                     cookie_store,
		shutdownWait:              20 * time.Second,
		hostname:                  hostname,
		databaseConn:              databaseConn,
		database:                  databaseClient,
		articleConn:               articleConn,
		article:                   articleClient,
		followsConn:               followsConn,
		follows:                   followsClient,
		feedConn:                  feedConn,
		feed:                      feedClient,
		createConn:                createConn,
		create:                    createClient,
		usersConn:                 usersConn,
		users:                     usersClient,
		s2sUndoConn:               s2sUndoConn,
		s2sUndo:                   s2sUndoClient,
		s2sUpdateConn:             s2sUpdateConn,
		s2sUpdate:                 s2sUpdateClient,
		s2sFollowConn:             s2sFollowConn,
		s2sFollow:                 s2sFollowClient,
		s2sLikeConn:               s2sLikeConn,
		s2sLike:                   s2sLikeClient,
		announceConn:              announceConn,
		announce:                  announceClient,
		approver:                  approverClient,
		approverConn:              approverConn,
		ldNorm:                    ldNormClient,
		ldNormConn:                ldNormConn,
		rssConn:                   rssConn,
		rss:                       rssClient,
		followRecommendationsConn: followRecommendationsConn,
		followRecommendations:     followRecommendationsClient,
		actorsConn:                actorsConn,
		actors:                    actorsClient,
		searchConn:                searchConn,
		search:                    searchClient,
		postRecommendationsConn:   postRecommendationsConn,
		postRecommendations:       postRecommendationsClient,
	}
	s.setupRoutes()
	return s
}

func main() {
	log.Printf("Starting skinny server.\n")
	s := buildServerWrapper()

	// The following code is partially taken from this link:
	// https://github.com/gorilla/mux#graceful-shutdown
	// It lays out a way for a server to gracefully shutdown when a SIGINT
	// (Ctrl+C) or SIGTERM (kill) is received.
	// See also: https://gobyexample.com/signals

	go func() {
		if err := s.server.ListenAndServe(); err != nil {
			log.Println(err)
		}
	}()

	// Accept graceful shutdowns when quit via SIGINT or SIGTERM. Other signals
	// (eg. SIGKILL, SIGQUIT) will not be caught.
	// Docker sends a SIGTERM on shutdown.
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)

	// Block until we receive signal.
	<-c
	s.shutdown()
	os.Exit(0)
}
