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
mkdir -p /go/src/proto/article

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
  build_out/database/database.proto

echo "Building logger service"
cp -R services/logger build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/logger \
  --python_out=build_out/logger \
  --grpc_python_out=build_out/logger \
  build_out/logger/logger.proto

echo "Building follows service"
cp -R services/follows build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/follows \
  --python_out=build_out/follows \
  --grpc_python_out=build_out/follows \
  build_out/follows/follows.proto
python3 -m grpc_tools.protoc \
  -Ibuild_out/database \
  --python_out=build_out/follows \
  --grpc_python_out=build_out/follows \
  build_out/database/database.proto

echo "Building article service"
cp -R services/article build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/article \
  --python_out=build_out/article \
  --grpc_python_out=build_out/article \
  build_out/article/article.proto

echo "Building protos for Go"
# TODO(devoxel): fix this hell of manually building protos

mkdir -p /go/src/proto/database
protoc -I=services/database --go_out=plugins=grpc:"/go/src/proto/database" \
  services/database/*.proto

mkdir -p /go/src/proto/follows
protoc -I=services/follows --go_out=plugins=grpc:"/go/src/proto/follows" \
  services/follows/*.proto
protoc -I=build_out/article \
  --go_out=plugins=grpc:"/go/src/proto/article" \
  build_out/article/article.proto

mkdir -p /go/src/proto/feed
protoc -I=services/feed --go_out=plugins=grpc:"/go/src/proto/feed" \
  services/feed/feed.proto

echo "Building feed service"
go build -o build_out/feed services/feed/*.go

echo "Building skinny server"
go build -o build_out/skinny skinny/*.go

echo "Installing node.js dependencies"
cd chump && npm install && cd ..

echo "Building client"
cd chump && npm run build && cd ..
mv chump/dist build_out/chump_dist
