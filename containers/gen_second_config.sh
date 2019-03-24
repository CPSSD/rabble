#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

export RABBLE_SKINNY_HOST="skinny_2"
export RABBLE_SKINNY_PORT="1917"
export RABBLE_INSTANCE_ID="2"
export RABBLE_NETWORK_NAME="rabble_testnetwork"
export RABBLE_NETWORK_CONFIG="external: true"
export RABBLE_DBPATH="/repo/rabble2.db"
export RABBLE_EXTERNAL_ADDRESS="skinny_2:1917"

python3 build_out/containers/build_compose.py \
  --template="build_out/containers/docker-compose.tmpl.yml" \
  --output="build_out/containers/second.yml"
