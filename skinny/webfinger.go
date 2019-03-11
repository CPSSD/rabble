package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	pb "github.com/cpssd/rabble/services/proto"
	util "github.com/cpssd/rabble/services/utils"
	webfinger "github.com/writeas/go-webfinger"
)

func getFullHostname() string {
	hostname := os.Getenv("HOST_NAME")
	if hostname == "" {
		log.Fatal("HOST_NAME env var not set for skinny server.")
	}
	return hostname
}

func getStrippedHost() string {
	hostname := getFullHostname()
	// Strip the port away from the hostname.
	split := strings.SplitN(hostname, ":", 2)
	// This shouldn't ever happen, but let's be sure.
	if split == nil || len(split) == 0 {
		log.Fatalf("Cannot split hostname %#v, expecting 'HOST:PORT'",
			hostname)
	}
	return split[0]
}

func (s *serverWrapper) newWebfingerHandler() http.HandlerFunc {
	wf := webfinger.Default(&wfResolver{
		users:     s.database,
		hostname:  getStrippedHost(),
		debugHost: getFullHostname(),
	})
	wf.NoTLSHandler = nil
	return http.HandlerFunc(wf.Webfinger)
}

type wfResolver struct {
	users     util.UsersGetter
	hostname  string
	debugHost string
}

func (wf *wfResolver) subject(user *pb.UsersEntry) string {
	return fmt.Sprintf("acct:%s@%s", user.Handle, wf.hostname)
}

func (wf *wfResolver) genLinks(user *pb.UsersEntry) []webfinger.Link {
	// Add a special case for local debugging, where we won't have a "dot" in the
	// hostname.
	// This does assume that non debug rabble users are using HTTPs and a standard
	// port, but they're probably decent assumptions to make.
	host := wf.hostname
	protocol := "https"
	if !strings.Contains(wf.hostname, ".") {
		host = wf.debugHost
		protocol = "http"
	}

	//TODO: Add magic-public-key webfinger links.
	//TODO(sailslick): Add atom/rss feeds webfinger links.
	html := webfinger.Link{
		HRef: fmt.Sprintf("%s://%s/#/@%s", protocol, host, user.Handle),
		Rel:  "http://webfinger.net/rel/profile-page",
		Type: "text/html",
	}
	ap := webfinger.Link{
		HRef: fmt.Sprintf("%s://%s/ap/@%s", protocol, host, user.Handle),
		Rel:  "self",
		Type: "application/activity+json",
	}
	return []webfinger.Link{html, ap}
}

// FindUser finds the user given the username and hostname
func (wf *wfResolver) FindUser(handle string, host, requestHost string, r []webfinger.Rel) (*webfinger.Resource, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	// We only support looking up hosts that exist on our server.
	if host != wf.hostname {
		fmt.Printf("webfinger: lookup on %s, expecting %s", host, wf.hostname)
		return nil, util.UserNotFoundErr
	}

	u, err := util.GetAuthorFromDb(ctx, handle, "", true, 0, wf.users)
	if err != nil {
		fmt.Printf("webfinger: user request error: %v", err)
		return nil, err
	}

	res := &webfinger.Resource{
		Subject: wf.subject(u),
		Links:   wf.genLinks(u),
	}
	return res, nil
}

// DummyUser allows us to fake a user, to prevent user enumeration.
//
// TODO(devoxel): create realistic fakes rather than 404s
func (wf *wfResolver) DummyUser(username string, hostname string, r []webfinger.Rel) (*webfinger.Resource, error) {
	return nil, util.UserNotFoundErr
}

// IsNotFoundError returns true if the given error is a not found error.
func (wf *wfResolver) IsNotFoundError(err error) bool {
	return err == util.UserNotFoundErr
}
