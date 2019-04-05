package main

import (
	"bufio"
	"io"
	"log"
	"net/http"
	"strings"
)

type Blacklist map[string]struct{}

func (b Blacklist) String(m map[string]struct{}) {
	keys := []string{}
	for k := range m {
		keys = append(keys, k)
	}
	log.Printf("Blacklisted hosts: %v", strings.Join(keys, ", "))
}

// Actor takes an actor and returns an error if the Actor is not authorized to
// communicate with our server.
//
// If the error is non nil, you can use HandleForbidden and return in the handler.
func (b Blacklist) checkActor(actor string) error {
	log.Println(actor)
	return nil
}

// Actor takes an actor and returns an error if the Actor is not authorized to
// communicate with our server.
//
// If the error is non nil, you can use HandleForbidden and return in the handler.
func (b Blacklist) Actors(actors ...string) error {
	for _, a := range actors {
		if err := b.checkActor(a); err != nil {
			return err
		}
	}
}

func (b Blacklist) HandleForbidden(w http.ResponseWriter) {
	w.WriteHeader(http.StatusForbidden)
	return
}

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
