package main

import (
	"log"
	"net/http"
)

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
	r.HandleFunc("/c2s/preview_article", s.handlePreviewArticle())
	r.HandleFunc("/c2s/feed", s.handleFeed())
	r.HandleFunc("/c2s/feed/{username}", s.handleFeed())
	r.HandleFunc("/c2s/@{username}", s.handleFeedPerUser())
	r.HandleFunc("/c2s/@{username}/{article_id}", s.handlePerArticlePage())
	r.HandleFunc("/c2s/follow", s.handleFollow())
	r.HandleFunc("/c2s/rss_follow", s.handleRssFollow())
	r.HandleFunc("/c2s/register", s.handleRegister())
	r.HandleFunc("/c2s/login", s.handleLogin())
	r.HandleFunc("/c2s/logout", s.handleLogout())

	approvalHandler := s.handleApprovalActivity()
	// ActorInbox routes are routed based on the activity type
	s.actorInboxRouter = map[string]http.HandlerFunc{
		"create": s.handleCreateActivity(),
		"follow": s.handleFollowActivity(),
		"accept": approvalHandler,
		"reject": approvalHandler,
	}
	r.HandleFunc("/ap/@{username}/inbox", s.handleActorInbox())
}
