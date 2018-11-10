#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

export SKINNY_SERVER_PORT=1917
echo "Building docker-compose images"
docker-compose -p two -f secondServer.yml build

echo "Starting docker-compose"
docker-compose -p two -f secondServer.yml up
