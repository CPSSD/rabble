#!/usr/bin/env sh

set -e

echo "Example container image"
docker build \
  --tag example_ms:latest \
  --file ./example_microservice/Dockerfile \
  .

echo "Example container"
docker run \
  --rm -it \
  --volume $PWD:/repo \
  example_ms:latest

echo "Done"
