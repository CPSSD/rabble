package main

import (
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/gorilla/mux"
)

func newTestServerWrapper() *serverWrapper {
    // TODO(iandioch): Fake/mock instead of using real dependencies
    return buildServerWrapper()
}

func TestHandleNotImplemented(t *testing.T) {
    req, _ := http.NewRequest("GET", "/test", nil)
    res := httptest.NewRecorder()
    newTestServerWrapper().handleNotImplemented()(res, req)

    if res.Code != http.StatusNotImplemented {
        t.Errorf("Expected 501 Not Implemented, got %#v", res.Code)
    }
    if res.Body.String() != "Not Implemented\n" {
        t.Errorf("Expected 'Not Implemented' body, got %#v", res.Body.String())
    }
}

func TestHandleFollow(t *testing.T) {
    req, _ := http.NewRequest("GET", "/test", nil)
    res := httptest.NewRecorder()
    vars := map[string]string{
        "username": "testuser",
    }
    req = mux.SetURLVars(req, vars)
    newTestServerWrapper().handleFollow()(res, req)
    if res.Code != http.StatusOK {
        t.Errorf("Expected 200 OK, got %#v", res.Code)
    }
    if res.Body.String() != "Followed testuser\n" {
        t.Errorf("Expected 'Followed testuser' body, got %#v", res.Body.String())
    }
}
