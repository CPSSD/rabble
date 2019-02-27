#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

_PREFIX=$USER
if [ -z "$_PREFIX" ]
then
  echo 'The prefix for docker compose is by default the $USER variable.'
  echo "Ensure $USER is set correctly."
fi

echo "Downing any existing docker-compose instance"
docker-compose \
  -f build_out/containers/first.yml \
  --project-directory . \
  -p $_PREFIX \
  down

echo "Building docker-compose images"
docker-compose \
  -f build_out/containers/first.yml \
  --project-directory . \
  -p $_PREFIX \
  build

echo "Starting docker-compose"
docker-compose \
  -f build_out/containers/first.yml \
  --project-directory . \
  -p $_PREFIX \
  up

