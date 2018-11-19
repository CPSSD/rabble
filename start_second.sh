#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

export SKINNY_SERVER_PORT=1917
export SKINNY_SERVER_HOST=skinny2
echo "Building docker-compose images"
docker-compose -p two -f second-server.yml build

echo "Starting docker-compose"
docker-compose -p two -f second-server.yml up
