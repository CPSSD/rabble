#!/usr/bin/env sh

set -e

cd /repo

cd chump/ && npm run lint && npm run test && cd ..

# once we clean up the go build management, we should just be
# able to run go test /go/src/github.com/cppsd/rabble/...
# for all go dependencies

go test skinny/*.go

echo "Running tests for follows microservice"
python3 -m unittest discover -s services/follows/ -p "*_test.py"
