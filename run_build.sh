#!/usr/bin/env sh

set -e

echo "RM'ing $PWD/build_out"
rm -rf $PWD/build_out
mkdir $PWD/build_out

echo "Creating build container image"
docker build \
  --tag rabble_build:latest \
  --file ./build_container/Dockerfile \
  .

echo "Running build container"
docker run \
  --rm \
  --volume $PWD:/repo \
  rabble_build:latest

echo "Done build"
