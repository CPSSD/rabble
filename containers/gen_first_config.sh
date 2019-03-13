#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

export RABBLE_SKINNY_HOST="skinny_1"
export RABBLE_SKINNY_PORT="1916"
export RABBLE_INSTANCE_ID="1"
export RABBLE_NETWORK_NAME="testnetwork"
export RABBLE_NETWORK_CONFIG="driver: bridge"
export RABBLE_DBPATH="/repo/rabble.db"
export RABBLE_EXTERNAL_ADDRESS="rabble.network"

python3 build_out/containers/build_compose.py \
  --template="build_out/containers/docker-compose.tmpl.yml" \
  --output="build_out/containers/first.yml"

