FROM alpine:3.7

RUN mkdir -p /repo/

# Install dependencies
RUN apk add --no-cache --update musl-dev protobuf
RUN apk add --no-cache --update nodejs nodejs-npm chromium nss
RUN apk add --no-cache --update g++ go ca-certificates git \
  python3 python3-dev gcc g++ linux-headers make

# Install gRPC for Go
RUN mkdir /go/
ENV GOPATH "/go"
ENV PATH $PATH:/go/bin
RUN go get -u google.golang.org/grpc
RUN go get -u github.com/golang/protobuf/protoc-gen-go

# Install gRPC protobuf for python
RUN pip3 install grpcio grpcio-tools googleapis-common-protos

# Dependencies for skinny server
RUN go get -u \
  github.com/gorilla/mux \
  github.com/gorilla/sessions \
  github.com/gomarkdown/markdown \
  github.com/microcosm-cc/bluemonday \
  github.com/mmcdole/gofeed \
  github.com/blevesearch/bleve/...

# Dependencies for auth service
RUN apk add --no-cache libffi-dev
RUN pip3 install bcrypt

RUN apk add --no-cache --update protobuf-dev

# Add PYTHONPATH for when we run tests
ENV PYTHONPATH="/repo/build_out"

CMD ["/repo/build_container/entry.sh"]
