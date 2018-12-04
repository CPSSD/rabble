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

wget "http://snap.stanford.edu/data/soc-LiveJournal1.txt.gz"
gunzip "soc-LiveJournal1.txt.gz"

while read p; do
    echo $p
done < soc-LiveJournal1.txt

#create_user $_RH stanley

#follow $_RH pam jim

#create_article $_RH stanley
