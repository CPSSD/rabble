#!/usr/bin/env sh

set -e

cd /repo

cd chump/ && npm run lint && npm run test && cd ..

# once we clean up the go build management, we should just be
# able to run go test /go/src/github.com/cppsd/rabble/...
# for all go dependencies

go test skinny/*.go

echo "Running tests for follows microservice"
cd build_out/follows
python3 -m unittest discover
cd ../../

echo "Running tests for database microservice"
cd build_out/database
python3 -m unittest discover
cd ../../

