#!/usr/bin/env sh
set -e

# run_build.sh builds all of docker's build using the build_container.
# if _TEST_RABBLE is set, then it also runs the test script.

USER_ID=`id -u $USER`

REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -z "$REPO_ROOT" ]
then
  echo "Could not find root of repo"
  exit 1
fi

BUILD_OUT="$REPO_ROOT/build_out"
echo "RM'ing $BUILD_OUT"
rm -rf $BUILD_OUT
mkdir $BUILD_OUT

echo "Creating build container image"
docker build \
  --tag rabble_build:latest \
  --file $REPO_ROOT/build_container/Dockerfile \
  $REPO_ROOT/build_container

echo "Running build container"
docker run \
  --rm \
  --volume $REPO_ROOT:/repo \
  -e LOCAL_USER_ID=$USER_ID \
  -e TEST_RABBLE=$_TEST_RABBLE \
  rabble_build:latest

echo "Done build"
