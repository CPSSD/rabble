#!/usr/bin/env sh

set -e
cd /repo
mkdir -p build_out

echo "Running build"

# Add build commands here.
# The current working directory is the root of the repo.
# Write your output to the `build_out` directory

echo "Building skinny server"
go build -o build_out/skinny skinny/*.go

echo "Building example go-python microservice"
SRC_DIR=services/example_go_python_microservice
protoc -I=$SRC_DIR \
--python_out="services/example_go_python_microservice/python_docker" \
--go_out="services/example_go_python_microservice/go_docker" \
$SRC_DIR/greetingCard.proto
go build -o build_out/example_go services/example_go_python_microservice/**/*.go

echo "Building example binary"
g++ services/example_microservice/main.cc -o build_out/example_ms
