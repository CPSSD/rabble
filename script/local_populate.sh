#!/usr/bin/env sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -z "$REPO_ROOT" ]
then
  echo "Could not find root of repo"
  exit 1
fi

. $REPO_ROOT/script/rabble_utils.sh

_RH=localhost:1916

create_user $_RH jim
create_user $_RH dwight
create_user $_RH michael
create_user $_RH pam
create_user $_RH stanley

follow $_RH dwight michael
follow $_RH michael jim
follow $_RH michael pam
follow $_RH jim pam
follow $_RH pam jim

create_article $_RH jim
create_article $_RH dwight
create_article $_RH michael
create_article $_RH pam
create_article $_RH stanley
