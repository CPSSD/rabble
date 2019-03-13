# Rabble

## Building

### Requirements

The only requirement to build Rabble is to have docker installed.

### Steps

Run `run_build.sh` and the output binaries will be written to a `build_out`
directory.

### Configuration

There are a few parameters you can use to configure your Rabble instance.
To change these options set the corresponding environment variable when running
`run_build.sh`. Unset values have sensible defaults.

 - `RABBLE_SEARCH_TYPE`:
   - bleve (default)
   - simple-search
 - `RABBLE_FOLLOW_RECOMMENDER_METHOD`:
   - none (default)
   - surprise

## Running Rabble

After doing a build you can run Rabble by executing the `start.sh` script.
Docker and docker-compose are both requried.

NOTE: If you have made changes to a microservice it will only be rebuilt if its
context directory changes. To manually rebuild run
`docker-compose build --no-cache <service_name>`

## Adding a new microservice to the build

To add a new microservice follow these steps:
 - Add new build dependencies (compilers, libraries, ...) to `build_container/Dockerfile`
 - Add the build commands to `build_container/build.sh`
 - Create a Dockerfile in the microservice's directory that runs the microservice
 - Add the new service to `docker-compose.yml`
 - Test!

## Running Rabble in Production

To run Rabble on a production server, first go and edit your configs

| Config Path                     | Description                 |
| ------------------------------- | ----------------------------|
| `containers/gen_first_config.sh`| Build Environment Variables |
| `chump/rabble_config.js`        | Frontend constants          |

The most important environment variables to change are:
- **RABBLE_SKINNY_HOST** - this should be the domain of the your instance

To set up continuous integration, read 
[the redeploy instructions](https://github.com/CPSSD/rabble/blob/master/script/redeploy/README.md)
