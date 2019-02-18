# chump

A typescript client for rabble.

## local development

To develop without docker, you'll first need to install the
dependencies with `npm install`, and you'll need chromium for tests.

Note that currently live updating development server script will not work,
you'll need to start the whole stack in order to access the server side.

Run `./run_build.sh && ./start.sh` and navigate to `localhost:1916`.

## Notes about develpment

### User facing strings

Please put all user facing strings in the `rabble_config.json` file, that way they
can be easily changed by instance hosts for localisation or general customisation.

Examples of how to use the config file can be found in many places. `components/header.tsx`
for example.

## npm scripts

- `npm run start`: Start a live development server that updates on file changes.

- `npm run lint`: Lint the codebase.

- `npm run fix`: Lint the codebase and autofix.
  Be careful with this, `git add` your files first.

- `npm run test`: Run tests.
  This uses Chromium, which needs to be on your PATH.

- `num run build`: Build the javascript once, with development config.

- `npm run build:prod`: Build the javascript with production config.

- `npm run clean`: Remove the old bundle.js file.
