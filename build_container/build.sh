#!/usr/bin/env sh

set -e

if [ -z "$LOCAL_USER_ID" ]
then
  echo "ERROR: environment variable LOCAL_USER_ID does not exist."
  echo "It is needed to preserve the mounted filesystem."
  echo "See run_build.sh in the root of the project."
  exit 1
fi

cd /repo
mkdir -p build_out/
mkdir -p build_out/activities/

# If when the script exits (because of an error or otherwise) the following
# function runs. The exit code is preserved.
function chown_trap {
  echo "Fixing permissions"
  adduser -D -u $LOCAL_USER_ID user
  cd /repo
  chown -R user build_out
  chown -R user chump/node_modules
}
trap chown_trap EXIT

echo "Running build"

# Add build commands here.
# The current working directory is the root of the repo.
# Write your output to the `build_out` directory

echo "Building database service"
cp -R services/database build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/database \
  --python_out=build_out/database \
  --grpc_python_out=build_out/database \
  build_out/database/proto/database.proto

echo "Building follows service"
cp -R services/follows build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/follows \
  --python_out=build_out/follows \
  --grpc_python_out=build_out/follows \
  build_out/follows/proto/follows.proto
python3 -m grpc_tools.protoc \
  -Ibuild_out/database \
  --python_out=build_out/follows \
  --grpc_python_out=build_out/follows \
  build_out/database/proto/database.proto

echo "Building article service"
cp -R services/article build_out/
# article service is only python service that needs mdc
cp -R services/mdc build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/article \
  --python_out=build_out/article \
  --grpc_python_out=build_out/article \
  build_out/article/proto/article.proto
python3 -m grpc_tools.protoc \
  -Ibuild_out/database \
  --python_out=build_out/article \
  --grpc_python_out=build_out/article \
  build_out/database/proto/database.proto
python3 -m grpc_tools.protoc \
  -Ibuild_out/mdc \
  --python_out=build_out/article \
  --grpc_python_out=build_out/article \
  build_out/mdc/proto/mdc.proto
# HACK: we need to remove the top level directory mdc since a go binary is
# built in the directory with the same name.
rm -rf build_out/mdc 

echo "Building create service"
cp -R services/activities/create build_out/activities/
python3 -m grpc_tools.protoc \
  -Ibuild_out/activities/create \
  --python_out=build_out/activities/create \
  --grpc_python_out=build_out/activities/create \
  --python_out=build_out/article \
  --grpc_python_out=build_out/article \
  build_out/activities/create/proto/create.proto
python3 -m grpc_tools.protoc \
  -Ibuild_out/database \
  --python_out=build_out/activities/create \
  --grpc_python_out=build_out/activities/create \
  build_out/database/proto/database.proto

echo "Building logger service and lib"
cp -R services/logger build_out/
cp -R services/utils build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/logger \
  --python_out=build_out/utils \
  --grpc_python_out=build_out/utils \
  --python_out=build_out/logger \
  --grpc_python_out=build_out/logger \
  --python_out=build_out/follows \
  --grpc_python_out=build_out/follows \
  --python_out=build_out/database \
  --grpc_python_out=build_out/database \
  --python_out=build_out/article \
  --grpc_python_out=build_out/article \
  --python_out=build_out/activities/create \
  --grpc_python_out=build_out/activities/create \
  build_out/logger/proto/logger.proto
python3 -m grpc_tools.protoc \
  -Ibuild_out/database \
  --python_out=build_out/utils \
  --grpc_python_out=build_out/utils \
  build_out/database/proto/database.proto

echo "Building protos for Go"
# This generate compiled protos and place them in the repo.
# For example: services/database/database.proto when build, would
# create a new file in the same directory: database.pb.go
protoc -I. --go_out=plugins=grpc:"." services/database/proto/*.proto
protoc -I. --go_out=plugins=grpc:"." services/follows/proto/*.proto
protoc -I. --go_out=plugins=grpc:"." services/article/proto/*.proto
protoc -I. --go_out=plugins=grpc:"." services/feed/proto/*.proto
protoc -I. --go_out=plugins=grpc:"." services/mdc/proto/*.proto
protoc -I. --go_out=plugins=grpc:"." services/activities/create/proto/*.proto

echo "Creating go workspace"
mkdir -p /go/src/github.com/cpssd/
cp -R /repo /go/src/github.com/cpssd/rabble

echo "Building all go binaries"
rm /go/bin/*
go install github.com/cpssd/rabble/...
mv /go/bin/* build_out

echo "Installing node.js dependencies"
cd chump && npm install && cd ..

echo "Building client"
cd chump && npm run build && cd ..
mv chump/dist build_out/chump_dist
