#!/bin/bash

set -e

# Create the network if we don't have it yet
docker network inspect models >/dev/null 2>&1 || docker network create models

# Build the image based on the Dockerfile
docker build -t models-cli -f Dockerfile .

# Run All Containers
docker-compose run --rm --service-ports models-cli