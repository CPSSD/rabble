FROM alpine:3.7

RUN apk add --no-cache --update python3 python3-dev gcc g++ linux-headers make musl-dev

# Install gRPC & protobufs for Python
RUN pip3 install grpcio

CMD ["python3 /repo/services/example_go_python_microservice/python_docker/gRPC_example.py"]
