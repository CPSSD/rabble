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
DATASET_URL="http://snap.stanford.edu/data/soc-LiveJournal1.txt.gz"
NUM_USERS=1000

FILTER_SCRIPT="
import sys
MAX_ID = $NUM_USERS
follows=[]
for line in sys.stdin:
    if line[0] == '#' or len(line) == 0:
        continue
    follower, followee = map(int, line.split())
    if follower > MAX_ID:
        break
    if followee > MAX_ID:
        continue
    follows.append((follower, followee))

for a, b in follows:
    print(a, b)
"

wget -N $DATASET_URL
gunzip soc-LiveJournal1.txt.gz

# Create users & articles.
for i in $(seq 0 $NUM_USERS); do
    create_user $_RH $i && create_article $_RH $i && logout $_RH
done

# Add follows.
cat soc-LiveJournal1.txt | python3 -c "$FILTER_SCRIPT" > tmp.txt

while read p; do
    follow $_RH $p
done < tmp.txt
rm tmp.txt

rm soc-LiveJournal1.txt
