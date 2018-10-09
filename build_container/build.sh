#!/usr/bin/env sh

set -e
cd /repo
mkdir -p build_out

echo "Running build"

# Add build commands here.
# The current working directory is the root of the repo.
# Write your output to the `build_out` directory

echo "Building example binary"
g++ example_microservice/main.cc -o build_out/example

