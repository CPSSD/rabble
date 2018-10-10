FROM alpine:3.7

# Install dependencies then remove the cache
RUN apk add --no-cache --update g++ && \
    mkdir -p /repo/

CMD ["/repo/build_container/build.sh"]

