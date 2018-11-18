#!/usr/bin/env sh

# Create user test
curl --request POST \
  --header "Content-Type: application/json" \
  --data '{"handle":"test","displayName":"test","password":"test","bio":"B"}' \
  "127.0.0.1:1916/c2s/register"

# Create user admin
curl --request POST \
  --header "Content-Type: application/json" \
  --data '{"handle":"admin","displayName":"admin","password":"admin","bio":"B"}' \
  "127.0.0.1:1916/c2s/register"

# follow user test with foreign user admin
curl --header "Content-Type: application/json" \
--request POST \
--data '{"follower":"admin@skinny2:1917", "followed":"test"}' \
127.0.0.1:1916/c2s/follow

# follow user test with foreign user admin on foreign server
curl --header "Content-Type: application/json" \
--request POST \
--data '{"follower":"admin", "followed":"test@skinny:1916"}' \
127.0.0.1:1917/c2s/follow

# Create a new article
DT=$(date '+%Y-%m-%dT%H:%M:%S.%3NZ')
curl --header "Content-Type: application/json" \
--request POST \
--data '{"author":"test", "body":"shoulders", "title":"head", "creation_datetime":"'$DT'"}' \
127.0.0.1:1916/c2s/create_article
