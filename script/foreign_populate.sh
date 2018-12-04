#!/usr/bin/env sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -z "$REPO_ROOT" ]
then
  echo "Could not find root of repo"
  exit 1
fi

. $REPO_ROOT/script/rabble_utils.sh

LOCAL=localhost:1916
FOREIGN=localhost:1917

RLOCAL=skinny:1916
RFOREIGN=skinny2:1917

create_user $LOCAL aaron
create_user $FOREIGN ross

follow $LOCAL aaron ross@$RFOREIGN
sleep 1

create_article $LOCAL aaron
create_article $FOREIGN ross
