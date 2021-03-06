#!/usr/bin/env sh

# $debug is used in order to find out what we're sending, in the case we're
# not getting expected results. To use it, just uncomment the debug line.
debug=
#debug=echo

create_user() {
  # Creates a user on a specified rabble instance.
  #
  # Arguments:
  #   1: domain - the rabble host (including port).
  #   2: username - the username for the user.
  #
  # Example:
  #   create_user localhost:1916 user
  $debug curl --request POST \
    --header "Content-Type: application/json" \
    --data '{"handle":"'"$2"'","displayName":"'"$2"'","password":"'"$2"'","bio":"bio!"}' \
    "$1/c2s/register"

}

login() {
  # Login to a rabble instance
  # Arguments:
  #   1: domain - the rabble host (including port).
  #   2: username - the rabble user (created with script)
  $debug curl -j -c localsession.db \
    --header "Content-Type: application/json" \
    --request POST \
    --data '{"handle":"'"$2"'", "password":"'"$2"'"}' \
    "$1/c2s/login"
}

like() {
  # Like an article on a rabble instance
  # Arguments:
  #   1: domain - the rabble host (including port).
  #   2: username - the rabble user (created with script)
  #   3: article_id - the ID of the article to like.
  login "$1" "$2"
  $debug curl -b localsession.db \
    --header "Content-Type: application/json" \
    --request POST \
    --data '{"article_id": '"$3"'}' \
    "$1/c2s/like"
}

per_article() {
  # Call the per-article endpoint to get a single article
  # Arguments:
  #   1: domain - the rabble host (including port).
  #   2: article_user - the rabble user (created with script)
  #   3: article_id - the ID of the article.
  #   4: login_user - Optional, login as this user
  if ! [ -z "$4" ]; then
    login "$1" "$4"
    $debug curl -b localsession.db "$1/c2s/@$2/$3"
  else
    $debug curl "$1/c2s/@$2/$3"
  fi
}

logout() {
  # Log out of a rabble instance
  # Arguments:
  #   1: domain - the rabble host (including port).
  $debug curl -j -c localsession.db "$1/c2s/logout"
}

follow() {
  # Follow a user on a specified rabble instance.
  #
  # Arguments:
  #   1: domain - the rabble host (including port).
  #   2: follower - the username for the follower
  #      this should also include an "@.." for foreign users.
  #   3: followed - the user being followed.
  #
  # Example:
  #   follow localhost:1916 admin@skinny.com:1917 user
  login "$1" "$2"
  $debug curl -b localsession.db \
    --header "Content-Type: application/json" \
    --request POST \
    --data '{"follower":"'"$2"'", "followed":"'"$3"'"}' \
    "$1/c2s/follow"
}

create_article() {
  # Create an article for a specified rabble instance.
  #
  # Arguments:
  #   1: domain - the rabble host (including port).
  #   2: author - the author of the article
  #
  # Example:
  #   follow localhost:1916 user
  login "$1" "$2"
  _title="update from $2"
  _body="it's me, $2, and i'm very bored."

  DT=$(date '+%Y-%m-%dT%H:%M:%S.%3NZ')
  $debug curl -b localsession.db \
    --header "Content-Type: application/json" \
    --request POST \
    --data '{"author":"'"$2"'", "body":"'"$_body"'", "title":"'"$_title"'", "creation_datetime":"'"$DT"'"}' \
    "$1/c2s/create_article"
}
