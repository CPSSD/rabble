FROM alpine:3.7

RUN mkdir -p /repo/

# Install dependencies
RUN apk add --no-cache --update musl-dev protobuf
RUN apk add --no-cache --update nodejs nodejs-npm
RUN apk add --no-cache --update g++ go ca-certificates git \
  python3 python3-dev gcc g++ linux-headers make

# Install gRPC for Go
RUN mkdir /go/
ENV GOPATH "/go:/repo:/repo/build_out"
ENV PATH $PATH:/go/bin
RUN go get -u google.golang.org/grpc
RUN go get -u github.com/golang/protobuf/protoc-gen-go

# Install gRPC protobuf for python
RUN pip3 install grpcio grpcio-tools googleapis-common-protos

# Dependencies for skinny server
RUN go get -u github.com/gorilla/mux

CMD ["/repo/build_container/entry.sh"]