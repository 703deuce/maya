# RunPod Endpoint Setup Instructions

## Current Status

✅ **Endpoint is configured and accepting requests**
- Endpoint URL: `https://api.runpod.ai/v2/o10i3yz4aaajfc/run`
- API Key: Configured
- Jobs are being queued but not processing (likely Docker image not deployed yet)

## Steps to Deploy

### Option 1: Deploy via GitHub Actions (Recommended)

1. **Set GitHub Secrets** (Settings → Secrets and variables → Actions):
   ```
   DOCKER_HUB_USERNAME=your-dockerhub-username
   DOCKER_HUB_TOKEN=your-dockerhub-token
   FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
   FIREBASE_STORAGE_BUCKET=aitts-d4c6d.firebasestorage.app (optional)
   ```

2. **Push to GitHub** (Already done ✅)
   ```bash
   git push origin main
   ```

3. **Wait for GitHub Actions** to build the Docker image
   - Check: https://github.com/703deuce/maya/actions
   - The workflow will build and push to Docker Hub

4. **Update RunPod Endpoint** with the Docker image:
   - Go to RunPod Dashboard → Serverless → Endpoints
   - Find endpoint ID: `o10i3yz4aaajfc`
   - Update Docker image to: `your-username/maya1-runpod-serverless:latest`
   - Set environment variables:
     - `FIREBASE_SERVICE_ACCOUNT_KEY` (your Firebase JSON)
     - `FIREBASE_STORAGE_BUCKET` (optional)

### Option 2: Manual Docker Build & Push

1. **Build Docker image locally:**
   ```bash
   docker build -t your-username/maya1-runpod-serverless .
   ```

2. **Push to Docker Hub:**
   ```bash
   docker login
   docker push your-username/maya1-runpod-serverless:latest
   ```

3. **Update RunPod Endpoint** (same as Step 4 above)

### Option 3: Direct Docker Hub Build

1. Connect your GitHub repo to Docker Hub (Settings → Builds)
2. Create automated build from `main` branch
3. Update RunPod endpoint with the resulting image

## Required Environment Variables in RunPod

When configuring the endpoint in RunPod dashboard, add these environment variables:

1. **FIREBASE_SERVICE_ACCOUNT_KEY** (Required for Firebase upload)
   - Full JSON service account key as a single-line string
   - Format: `{"type":"service_account","project_id":"...",...}`

2. **FIREBASE_STORAGE_BUCKET** (Optional)
   - Default: `aitts-d4c6d.firebasestorage.app`

3. **MODEL_NAME** (Optional)
   - Default: `maya-research/maya1`

## Testing the Endpoint

Once the Docker image is deployed:

1. **Run simple test:**
   ```bash
   python test_simple.py
   ```

2. **Run comprehensive test:**
   ```bash
   python test_runpod_endpoint.py
   ```

3. **Check endpoint diagnostics:**
   ```bash
   python test_diagnostic.py
   ```

## Troubleshooting

### Jobs stuck in IN_QUEUE

- **Check RunPod logs**: Dashboard → Endpoints → Your endpoint → Logs
- **Verify Docker image**: Ensure image exists and is accessible
- **Check GPU availability**: Ensure endpoint has GPU workers available
- **Verify handler.py**: Check that the handler is properly configured

### Handler errors

- Check RunPod worker logs for Python errors
- Verify all dependencies are in `requirements.txt`
- Ensure Firebase credentials are correctly formatted (single-line JSON)

### Model loading issues

- First request will be slow (cold start while downloading model)
- Ensure sufficient GPU memory (16GB+ VRAM recommended)
- Check HuggingFace model access (may need authentication)

## Expected Response Format

Success response:
```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "output": {
    "audio_base64": "...",
    "sampling_rate": 24000,
    "duration": 2.5,
    "format": "wav",
    "content_type": "audio/wav"
  }
}
```

Error response:
```json
{
  "id": "job-id",
  "status": "FAILED",
  "error": "Error message here"
}
```

## Next Steps

1. ✅ Code pushed to GitHub
2. ⏳ Build Docker image (via GitHub Actions or manually)
3. ⏳ Deploy Docker image to RunPod endpoint
4. ⏳ Configure environment variables in RunPod
5. ⏳ Test endpoint with test scripts
6. ⏳ Monitor logs for any issues

