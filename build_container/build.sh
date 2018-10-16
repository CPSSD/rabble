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
mkdir -p /go/src/greetingCard

echo "Running build"

# Add build commands here.
# The current working directory is the root of the repo.
# Write your output to the `build_out` directory

echo "Building skinny server"
go build -o build_out/skinny skinny/*.go

echo "Building database service"
cp -R services/database build_out/
python3 -m grpc_tools.protoc \
  -Ibuild_out/database \
  --python_out=build_out/database \
  --grpc_python_out=build_out/database \
  build_out/database/database.proto

echo "Building example go microservice"
SRC_DIR=services/example_go_python_microservice
protoc -I=$SRC_DIR \
--go_out=plugins=grpc:"/go/src/greetingCard" \
$SRC_DIR/greetingCard.proto
go build -o build_out/example_go services/example_go_python_microservice/go/*.go

echo "Building example Protobuf for python"
PYTHON_OUT_DIR="build_out"
python3 -m grpc_tools.protoc -I$SRC_DIR --python_out=$PYTHON_OUT_DIR \
--grpc_python_out=$PYTHON_OUT_DIR $SRC_DIR/greetingCard.proto

echo "Copying python files for example microservice"
cp services/example_go_python_microservice/python/*.py $PYTHON_OUT_DIR

echo "Building example binary"
g++ services/example_microservice/main.cc -o build_out/example_ms

echo "Installing node.js dependencies"
cd fatty && npm install && cd ..

echo "Building client"
cd fatty && npm run build && cd ..
mv fatty/dist build_out/fatty_dist

echo "Fixing permissions"
adduser -D -u $LOCAL_USER_ID user
chown -R user build_out
chown -R user fatty/node_modules
