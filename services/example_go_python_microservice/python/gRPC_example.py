import greetingCard_pb2
import greetingCard_pb2_grpc
import grpc
import os
import sys

def send_greeting_card(stub, msg, sender, gift):
    gc = greetingCard_pb2.GreetingCard(sender=sender, letter=msg, money_enclosed=gift)
    acknowledge_card = stub.GetGreetingCard(gc)

    if not acknowledge_card.letter:
        print("No message in AcknowledgmentCard")
        return

    print("Received: " + acknowledge_card.letter)

def main():
    go_host = os.environ["GO_SERVER_HOST"]
    if not go_host:
        print("Please set GO_SERVER_HOST env variable")
        sys.exit(1)
    go_server_address = go_host + ":8000"

    print("Connecting to " + go_server_address)
    with grpc.insecure_channel(go_server_address) as channel:
        stub = greetingCard_pb2_grpc.GreetingCardsStub(channel)
        print("Sending greeting card")
        send_greeting_card(stub, "Happy Bday", "Sacha Baron Cohen", 0)


if __name__ == "__main__":
    main()
