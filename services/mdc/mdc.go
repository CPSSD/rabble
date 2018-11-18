package main

import (
	"context"
	"log"
	"net"

	pb "github.com/cpssd/rabble/services/proto/gopb"
	"github.com/gomarkdown/markdown"
	"github.com/microcosm-cc/bluemonday"
	"google.golang.org/grpc"
)

type MDServer struct {
	sanitizer *bluemonday.Policy
}

func newMDServer() *MDServer {
	policy := bluemonday.UGCPolicy()
	return &MDServer{sanitizer: policy}
}

func (s *MDServer) MarkdownToHTML(ctx context.Context, r *pb.MDRequest) (*pb.MDResponse, error) {
	unsafe := markdown.ToHTML([]byte(r.MdBody), nil, nil)
	html := s.sanitizer.SanitizeBytes(unsafe)
	return &pb.MDResponse{HtmlBody: string(html)}, nil
}

func main() {
	log.Print("Starting markdown converter.")

	lis, err := net.Listen("tcp", ":1937")
	if err != nil {
		log.Fatalf("failed to listen to 0.0.0.0:1937: %v", err)
	}

	grpcSrv := grpc.NewServer()
	pb.RegisterConverterServer(grpcSrv, newMDServer())
	grpcSrv.Serve(lis)
}
