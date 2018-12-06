#!/usr/bin/env sh

set -e

if [ ! -d "build_out" ]
then
  echo "build_out doesn't exist, run a build first"
  exit 1
fi

export SKINNY_SERVER_PORT=1916
export SKINNY_SERVER_HOST=skinny

echo "Downing any existing docker-compose instance"
docker-compose down

echo "Building docker-compose images"
docker-compose -p rabble build

echo "Starting docker-compose"
docker-compose -p rabble up
