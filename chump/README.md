# Chump

A typescript client for Rabble.

## Local Development

To develop without docker, you'll first need to install the
dependencies with `npm install`, and you'll need chromium for tests.

After that, you can use the npm scripts to run a local live server,
or build the javascript.

- `npm run start`: Start a live development server that updates on file changes.

- `npm run lint`: Lint the codebase.

- `npm run fix`: Lint the codebase and autofix.
  Be careful with this, `git add` your files first.

- `npm run test`: Run tests.
  This uses Chromium, which needs to be on your PATH.

- `num run build`: Build the javascript once, with development config.

- `npm run build:prod`: Build the javascript with production config.

- `npm run clean`: Remove the old bundle.js file.
