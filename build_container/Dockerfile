FROM alpine:3.7

# Install dependencies then remove the cache
RUN apk add --no-cache --update g++ go unzip ca-certificates git && \
    mkdir -p /repo/


# Install gRPC & protobufs for Go
RUN go get -u google.golang.org/grpc
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protoc-3.6.1-linux-x86_64.zip
RUN unzip protoc-3.6.1-linux-x86_64.zip
RUN go get -u github.com/golang/protobuf/protoc-gen-go

CMD ["/repo/build_container/build.sh"]
