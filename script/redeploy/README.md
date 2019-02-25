# redeploy

This redeploy script is intended for use with rabble.network, but you could
modify it to work in any fork of Rabble.

## Usage

- Setup a systemd service file for your Rabble instance.
  See the example file (`rabble.service`) for inspiration.

- Ensure the user that run's the script has permissions to restart
  the rabble service without password input. This can be done by editing
  `/etc/sudoers` file using `visudo`.

  See [this StackOverflow question](https://askubuntu.com/a/1012015)
  for inspiration (and make sure to run `whereis systemctl` before using
  `/bin/systemctl`, as it varies by distribution.

- Add a read-only github deployment key if your instance isn't public.

- Specify the branch you'd like to use in `redepoly.sh` by setting `_BRANCH`

- Setup `redeploy.sh` to trigger on a server after a push to master.
  Usually done with a Github webhook.
  Ensure the working directory is set to somewhere inside the rabble repository.

  For rabble.network, this was done using [webhook](https://github.com/adnanh/webhook).
