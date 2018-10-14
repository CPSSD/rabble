package main

import (
	"fmt"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
	protobuf "greetingCard"
	"log"
	"net"
)

type server struct{}

func (s *server) GetGreetingCard(ctx context.Context, in *protobuf.GreetingCard) (*protobuf.AcknowledgmentCard, error) {
	fmt.Println("Got card from " + in.Sender)
	return &protobuf.AcknowledgmentCard{Letter: "Thank you for the card, " + in.Sender}, nil
}

func main() {
	lis, err := net.Listen("tcp", "8000")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	protobuf.RegisterGreetingCardsServer(grpcServer, &server{})
	grpcServer.Serve(lis)
}
