#!/bin/bash

set -e

# Create the network if we don't have it yet
docker network inspect data-pipeline >/dev/null 2>&1 || docker network create data-pipeline

# Build the image based on the Dockerfile
docker build -t data-pipeline-cli -f Dockerfile .

# Run All Containers
docker-compose run --rm --service-ports data-pipeline-cli