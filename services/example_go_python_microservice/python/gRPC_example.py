import greetingCard_pb2
import greetingCard_pb2_grpc
import grpc

def send_greeting_card(stub, msg, sender, gift):
    gc = greetingCard_pb2.GreetingCard(sender=sender, letter=msg, money_enclosed=gift)
    acknowledge_card = stub.GetGreetingCard(gc)

    if not acknowledge_card.letter:
        print("No message in AcknowledgmentCard")
        return

    print("Received: " + acknowledge_card.letter)

def main():
    with grpc.insecure_channel('8000') as channel:
        stub = greetingCard_pb2_grpc.GreetingCardsStub(channel)
        print("Sending greeting card")
        send_greeting_card(stub, "Happy Bday", "Sacha Baron Cohen", 0)


if __name__ == "__main__":
    main()
