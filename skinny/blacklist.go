package main

import (
	"bufio"
	"bytes"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"strings"
)

func loadBlacklistFile() io.Reader {
	path := os.Getenv("BLACKLIST_FILE")
	if path == "" {
		log.Fatalln("BLACKLIST_FILE env var not set for skinny server.")
	}

	b, err := ioutil.ReadFile(path)
	if err != nil {
		log.Fatalf("blacklist file: %v", err)
	}

	return bytes.NewReader(b)
}

// Blacklist type defines the format of the Rabble blacklist
// URIs are mapped to empty structs
type Blacklist map[string]struct{}

func (b Blacklist) String(m map[string]struct{}) {
	keys := []string{}
	for k := range m {
		keys = append(keys, k)
	}
	log.Printf("Blacklisted hosts: %v", strings.Join(keys, ", "))
}

// Actor takes an actor and returns a boolean indicating if the actor is
// blacklisted.
func (b Blacklist) actorBlacklisted(actor string) (bool, error) {
	u, err := url.Parse(actor)
	if err != nil {
		return false, err
	}

	if _, exists := b[u.Host]; exists {
		return true, nil
	}

	return false, nil
}

// Actors takes an actor from an Activity and returns true if the actor was blacklisted.
//
// This function takes place of handling of errors, so no additional
// status/etc are required.
func (b Blacklist) Actors(w http.ResponseWriter, actors ...string) bool {
	for _, a := range actors {
		if bad, err := b.actorBlacklisted(a); bad || err != nil {
			b.HandleForbidden(w, err)
			return true
		}
	}
	return false
}

// HandleForbidden will return the correct status code based on whether
// there was an error or access was denied
func (b Blacklist) HandleForbidden(w http.ResponseWriter, err error) {
	if err != nil {
		log.Printf("Error in blacklist: %v", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	log.Println("Received an activity from a blacklisted instance.")
	w.WriteHeader(http.StatusForbidden)
	return
}

// NewBlacklist reads in the config blacklist
func NewBlacklist(r io.Reader) Blacklist {
	blacklisted := map[string]struct{}{}
	scanner := bufio.NewScanner(r)
	for scanner.Scan() {
		l := strings.TrimSpace(scanner.Text())

		// Handle comments.
		if len(l) == 0 || l[0] == '#' {
			continue
		}

		// Handle inline comments.
		if i := strings.Index(l, "#"); i != -1 {
			l = strings.TrimSpace(l[0:i])
		}

		blacklisted[l] = struct{}{}
	}
	if err := scanner.Err(); err != nil {
		log.Fatalf("error reading blacklist file: %v", err)
	}
	return blacklisted
}
