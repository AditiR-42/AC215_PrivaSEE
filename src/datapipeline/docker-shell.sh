#!/bin/bash

set -e  # Exit on any error

# Define variables
NETWORK_NAME="data-containerization-network"
CONTAINER_NAME="data-label-studio"
IMAGE_NAME="custom-label-studio:latest"

# Step 1: Create the Docker network if it doesn't exist
docker network inspect "$NETWORK_NAME" >/dev/null 2>&1 || docker network create "$NETWORK_NAME"

# Step 2: Build the Docker image from the Dockerfile
echo "Building Docker image..."
docker build -t "$IMAGE_NAME" .

# Step 3: Stop and remove any existing container with the same name
echo "Stopping and removing existing container (if any)..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Step 4: Run the Docker container with a long-running command
echo "Running Docker container..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --network "$NETWORK_NAME" \
  -p 8080:8080 \
  -v "$(pwd)/../secrets:/secrets" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/secrets/model-containerization.json" \
  -e GCP_PROJECT="ac215-privasee" \
  -e GCP_ZONE="us-central1-a" \
  "$IMAGE_NAME" tail -f /dev/null
