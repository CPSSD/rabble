#!/usr/bin/env sh

set -e

cd /repo

cd chump/ && npm run lint && npm run test && cd ..

echo "Running go tests"
go test github.com/cpssd/rabble/...

echo "Running python unit tests for activites/undo"
cd build_out/activities/undo
python3 -B -m unittest discover
cd ../../../

echo "Running python unit tests for containers/"
cd build_out/containers
python3 -B -m unittest discover
cd ../../

echo "Running python unit tests for utils/"
cd build_out/utils
python3 -B -m unittest discover
cd ../../

echo "Running python unit tests for users/"
cd build_out/users
python3 -B -m unittest discover
cd ../../

echo "Running tests for database microservice"
cd build_out/database
python3 -B -m unittest discover
cd ../../

echo "Running tests for follows"
cd build_out/follows
python3 -B -m unittest discover
cd ../../

echo "Running python unit tests for activities/follow"
cd build_out/activities/follow
python3 -B -m unittest discover
cd ../../../

echo "Running python unit tests for activities/like"
cd build_out/activities/like
python3 -B -m unittest discover
cd ../../../
