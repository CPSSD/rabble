# Rabble

## Building

The only requirement to build Rabble is to have docker installed.
Run `run_build.sh` and the output binaries will be written to a `build_out`
directory.

## Running Rabble

After doing a build you can run Rabble by executing the `start.sh` script.
Docker and docker-compose are both requried.

## Adding a new microservice to the build

To add a new microservice follow these steps:
 - Add the build dependencies (compilers, libraries, ...) to `build_container/Dockerfile`
 - Add the build commands to `build_container/build.sh`
 - Create a Dockerfile in the microservice's directory that runs the microservice
 - Add the new service to `docker-compose.yml`
 - Test!

