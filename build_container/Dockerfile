FROM alpine:3.7

# Install dependencies then remove the cache
RUN apk add --no-cache --update g++ go ca-certificates git protobuf && \
    mkdir -p /repo/


# Install gRPC for Go
RUN mkdir /go/
ENV GOPATH "/go"
ENV PATH $PATH:$GOPATH/bin
RUN go get -u google.golang.org/grpc
RUN go get -u github.com/golang/protobuf/protoc-gen-go

CMD ["/repo/build_container/build.sh"]
