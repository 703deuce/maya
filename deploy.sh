#!/bin/bash
# Helper script to deploy Maya1 to RunPod Serverless
# Usage: ./deploy.sh [docker-image-tag]

set -e

DOCKER_IMAGE="${1:-your-username/maya1-runpod-serverless:latest}"
ENDPOINT_ID="${RUNPOD_ENDPOINT_ID:-}"

if [ -z "$ENDPOINT_ID" ]; then
    echo "Error: RUNPOD_ENDPOINT_ID environment variable not set"
    echo "Usage: RUNPOD_ENDPOINT_ID=your-endpoint-id ./deploy.sh [docker-image]"
    exit 1
fi

if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Error: RUNPOD_API_KEY environment variable not set"
    exit 1
fi

echo "Deploying $DOCKER_IMAGE to RunPod endpoint $ENDPOINT_ID"

# Note: This is a placeholder. Actual RunPod API may vary.
# Check RunPod documentation for the exact GraphQL mutation for serverless endpoints.
# You may need to update the endpoint via RunPod dashboard or use their CLI.

echo "Please update your RunPod serverless endpoint manually:"
echo "1. Go to RunPod dashboard > Serverless > Endpoints"
echo "2. Select your endpoint"
echo "3. Update Docker image to: $DOCKER_IMAGE"
echo "4. Ensure environment variables are set:"
echo "   - FIREBASE_SERVICE_ACCOUNT_KEY"
echo "   - FIREBASE_STORAGE_BUCKET"

# Alternative: Use RunPod Python SDK if available
# pip install runpod
# runpod update_endpoint --endpoint-id $ENDPOINT_ID --docker-image $DOCKER_IMAGE

