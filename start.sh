#!/usr/bin/env sh

set -e

echo "Building docker-compose images"
docker-compose build

echo "Starting docker-compose"
docker-compose up
