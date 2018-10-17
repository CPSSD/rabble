#!/usr/bin/env sh

set -e

export LOCAL_USER_ID
export TEST_RABBLE

/repo/build_container/build.sh

if [ -n "${TEST_RABBLE}" ]
then
  /repo/build_container/test.sh
fi
