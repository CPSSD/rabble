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

echo "Building example binary"
g++ services/example_microservice/main.cc -o build_out/example_ms
