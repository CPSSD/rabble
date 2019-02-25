# redeploy

This redeploy script is intended for use with rabble.network, but you could
modify it to work in any fork of rabble.

## Usage

- Setup a systemd service file for your Rabble instance.
  See the example file for inspiration.

- Add a read-only github deployment key if you're instance isn't public.

- If you an instance config you don't want in master, specify the branch to use in
  `redepoly.sh`

- Setup `redeploy.sh` to trigger on a server after a push to master.
  Usually done with a Github webhook.
  Ensure the working directory is set to somewhere inside the rabble repository.

  For rabble.network, this was done using [webhook](https://github.com/adnanh/webhook).
