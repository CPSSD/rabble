set -e

# Set _BRANCH to the branch you'd like keep updated to master.
_BRANCH="deploy/rabblenetwork"

REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ -z "$REPO_ROOT" ]
then
  echo "Could not find root of repo"
  exit 1
fi

cd $REPO_ROOT
git checkout master
git pull origin
git checkout $_BRANCH

# TODO(devoxel): Add a special trigger to reload the database if a
# certain string is in the commit diff
git rebase master

$REPO_ROOT/run_build.sh
sudo systemctl restart rabble
