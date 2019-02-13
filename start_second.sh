#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

echo "Downing any existing docker-compose instance"
docker-compose \
  -f build_out/containers/second.yml \
  --project-directory . \
  -p two \
  down

echo "Building docker-compose images"
docker-compose \
  -f build_out/containers/second.yml \
  --project-directory . \
  -p two \
  build

echo "Starting docker-compose"
docker-compose \
  -f build_out/containers/second.yml \
  --project-directory . \
  -p two \
  up

