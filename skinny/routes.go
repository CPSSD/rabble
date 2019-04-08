package main

import (
	"log"
	"net/http"
	"os"

	webfinger "github.com/writeas/go-webfinger"
)

const (
	noOpLocation             = "./services/noop"
	postServiceLocationEnv   = "POST_RECOMMENDATIONS_NO_OP"
	followServiceLocationEnv = "FOLLOW_RECOMMENDATIONS_NO_OP"
)

func (s *serverWrapper) getNoOpServiceHandler(env string, defaultFunc http.HandlerFunc) http.HandlerFunc {
	serviceLocation := os.Getenv(env)
	if serviceLocation == noOpLocation {
		return s.handleNoOp()
	}
	return defaultFunc
}

// setupRoutes specifies the routing of all endpoints on the server.
// Centralised routing config allows easier debugging of a specific endpoint,
// as the code handling it can be looked up here.
// The server uses mux for routing. See instructions and examples for mux at
// https://www.gorillatoolkit.org/pkg/mux .
func (s *serverWrapper) setupRoutes() {
	const (
		assetPath = "/assets/"
	)
	log.Printf("Setting up routes on skinny server.\n")

	r := s.router
	fs := http.StripPrefix(assetPath, http.FileServer(http.Dir(staticAssets)))

	r.PathPrefix(assetPath).Handler(fs)

	// User-facing routes
	r.HandleFunc("/", s.handleIndex())

	// c2s routes
	r.HandleFunc("/c2s/create_article", s.handleCreateArticle())
	r.HandleFunc("/c2s/edit_article", s.handleEditArticle())
	r.HandleFunc("/c2s/delete_article", s.handleDeleteArticle())
	r.HandleFunc("/c2s/preview_article", s.handlePreviewArticle())
	r.HandleFunc("/c2s/feed", s.handleFeed())
	r.HandleFunc("/c2s/feed/{userId}", s.handleFeed())
	r.HandleFunc("/c2s/@{username}", s.handleFeedPerUser())
	r.HandleFunc("/c2s/{userId}/rss", s.handleRssPerUser())
	r.HandleFunc("/c2s/{userId}/css", s.handleUserCss())
	r.HandleFunc("/c2s/article/{article_id}", s.handlePerArticlePage())
	r.HandleFunc("/c2s/@{username}/followers", s.handleGetFollowers())
	r.HandleFunc("/c2s/@{username}/following", s.handleGetFollowing())

	// TODO(sailslick): move these below after user_id change comes in
	// That change will stop perArticle from catching all urls
	// These may be no-op services
	r.HandleFunc("/c2s/{userId}/recommend_follows",
		s.getNoOpServiceHandler(followServiceLocationEnv, s.handleRecommendFollows()))
	r.HandleFunc("/c2s/recommend_posts",
		s.getNoOpServiceHandler(postServiceLocationEnv, s.handlePostRecommendations()))

	r.HandleFunc("/c2s/follow", s.handleFollow())
	r.HandleFunc("/c2s/unfollow", s.handleUnfollow())
	r.HandleFunc("/c2s/rss_follow", s.handleRssFollow())
	r.HandleFunc("/c2s/register", s.handleRegister())
	r.HandleFunc("/c2s/search", s.handleSearch())
	r.HandleFunc("/c2s/login", s.handleLogin())
	r.HandleFunc("/c2s/logout", s.handleLogout())
	r.HandleFunc("/c2s/like", s.handleLike())
	r.HandleFunc("/c2s/update/user", s.handleUserUpdate())
	r.HandleFunc("/c2s/update/user_pic", s.handleUserUpdateProfilePic())
	r.HandleFunc("/c2s/details/user", s.handleUserDetails())
	r.HandleFunc("/c2s/follows/pending", s.handlePendingFollows())
	r.HandleFunc("/c2s/follows/accept", s.handleAcceptFollow())
	r.HandleFunc("/c2s/track_view", s.handleTrackView())
	r.HandleFunc("/c2s/add_log", s.handleAddLog())
	r.HandleFunc("/c2s/announce", s.handleAnnounce())

	approvalHandler := s.handleApprovalActivity()
	// ActorInbox routes are routed based on the activity type
	s.actorInboxRouter = map[string]http.HandlerFunc{
		"create":   s.handleCreateActivity(),
		"undo":     s.handleUndoActivity(),
		"follow":   s.handleFollowActivity(),
		"like":     s.handleLikeActivity(),
		"accept":   approvalHandler,
		"reject":   approvalHandler,
		"announce": s.handleAnnounceActivity(),
		"update":   s.handleUpdateActivity(),
	}
	s.undoActivityRouter = map[string]http.HandlerFunc{
		"like":   s.handleLikeUndoActivity(),
		"follow": s.handleFollowUndoActivity(),
	}
	r.HandleFunc("/ap/@{username}/inbox", s.handleActorInbox())
	r.HandleFunc("/ap/@{username}", s.handleActor())
	r.HandleFunc("/ap/@{username}/following", s.handleFollowingCollection())
	r.HandleFunc("/ap/@{username}/followers", s.handleFollowersCollection())

	r.HandleFunc(webfinger.WebFingerPath, s.newWebfingerHandler())
}
