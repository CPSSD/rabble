#!/usr/bin/env sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -z "$REPO_ROOT" ]
then
  echo "Could not find root of repo"
  exit 1
fi

. $REPO_ROOT/script/rabble_utils.sh

echo "This script depends on local_populate.sh being run first."

LOCAL=localhost:1916
FOREIGN=localhost:1917

RLOCAL=skinny:1916
RFOREIGN=skinny2:1917

create_user $FOREIGN david
follow $LOCAL dwight david@$RFOREIGN
create_article $FOREIGN david
