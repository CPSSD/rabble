#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

echo "Building docker-compose images"
docker-compose build

echo "Starting docker-compose"
docker-compose up
