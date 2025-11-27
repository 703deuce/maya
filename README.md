# Maya1 RunPod Serverless Endpoint

Production-ready RunPod serverless endpoint for the [Maya1 TTS model](https://huggingface.co/maya-research/maya1), enabling expressive voice generation with emotion tags and Firebase Storage integration.

## Features

- 🎙️ **Expressive Voice Generation**: Natural language voice descriptions
- 😊 **Emotion Tags**: Support for `<laugh>`, `<cry>`, `<whisper>`, `<angry>`, and 20+ more emotions
- 🔥 **Firebase Integration**: Direct upload to Firebase Storage
- ⚡ **Real-time Streaming**: SNAC codec for efficient audio generation
- 🐳 **Docker Ready**: Production-ready container with CUDA support
- 🚀 **CI/CD**: Automated deployment via GitHub Actions

## Architecture

- **Model**: Maya1 (3B parameters, Llama-based)
- **Audio Format**: 24 kHz WAV, base64-encoded
- **Codec**: SNAC neural codec (~0.98 kbps)
- **Framework**: RunPod Serverless

## Request Format

```json
{
  "input": {
    "text": "Hello world <laugh> this is amazing!",
    "voice_description": "Female, in her 30s with an American accent, energetic, clear diction",
    "temperature": 0.7,
    "max_new_tokens": 2000,
    "upload_to_firebase": true,
    "firebase_user_id": "user123"
  }
}
```

### Parameters

- `text` (required): Text to synthesize, can include emotion tags
- `voice_description` (optional): Natural language voice description (default: "Neutral voice, clear speech")
- `temperature` (optional): Sampling temperature, 0.0-1.0 (default: 0.7)
- `max_new_tokens` (optional): Maximum tokens to generate (default: 2000)
- `upload_to_firebase` (optional): Upload audio to Firebase Storage (default: false)
- `firebase_user_id` (required if `upload_to_firebase` is true): User ID for Firebase path

### Supported Emotion Tags

- `<laugh>`, `<laugh_harder>`
- `<cry>`, `<cry_harder>`
- `<whisper>`
- `<angry>`, `<rage>`
- `<giggle>`, `<chuckle>`
- `<gasp>`, `<sigh>`
- `<snort>`
- And more...

## Response Format

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "output": {
    "audio_base64": "UklGRn...",
    "sampling_rate": 24000,
    "duration": 2.5,
    "format": "wav",
    "content_type": "audio/wav",
    "firebase_url": "https://firebasestorage.googleapis.com/...",
    "firebase_path": "users/user123/tts/tts_1234567890_hello.wav",
    "firebase_filename": "tts_1234567890_hello.wav"
  }
}
```

## Local Development

### Prerequisites

- Docker with CUDA support
- Python 3.10+
- RunPod CLI (optional, for local testing)

### Build Docker Image

```bash
docker build -t maya1-runpod-serverless .
```

### Run Locally

```bash
docker run --gpus all -p 8000:8000 \
  -e FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}' \
  -e FIREBASE_STORAGE_BUCKET="aitts-d4c6d.firebasestorage.app" \
  maya1-runpod-serverless
```

### Test Endpoint

```bash
curl -X POST http://localhost:8000/runsync \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Hello, this is a test.",
      "voice_description": "Male, late 20s, neutral American, warm baritone",
      "upload_to_firebase": false
    }
  }'
```

## Deployment to RunPod

### Manual Deployment

1. Build and push Docker image to a registry (Docker Hub, etc.)
2. Create a RunPod serverless endpoint via RunPod dashboard
3. Configure environment variables:
   - `FIREBASE_SERVICE_ACCOUNT_KEY`: Firebase service account JSON
   - `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket (optional, defaults to `aitts-d4c6d.firebasestorage.app`)
   - `MODEL_NAME`: Override model name (optional, defaults to `maya-research/maya1`)

### GitHub Actions Deployment

1. Set up GitHub Secrets:
   - `RUNPOD_API_KEY`: Your RunPod API key
   - `RUNPOD_ENDPOINT_ID`: Your RunPod endpoint ID
   - `DOCKER_HUB_USERNAME`: Docker Hub username
   - `DOCKER_HUB_TOKEN`: Docker Hub access token
   - `FIREBASE_SERVICE_ACCOUNT_KEY`: Firebase service account JSON (single-line)
   - `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket (optional)

2. Push to `main` branch to trigger deployment

3. The workflow will:
   - Build Docker image
   - Push to Docker Hub
   - Deploy to RunPod serverless endpoint

### RunPod Endpoint Configuration

- **GPU**: Minimum 1x GPU (A100, H100, or RTX 4090 recommended)
- **VRAM**: 16GB+ required
- **Memory**: 15GB+ RAM
- **Storage**: 20GB volume, 10GB container disk
- **Port**: 8000 (HTTP)

## Environment Variables

### Required (for Firebase upload)

- `FIREBASE_SERVICE_ACCOUNT_KEY`: Full Firebase service account JSON as a single string
  ```json
  {"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}
  ```

### Optional

- `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket (default: `aitts-d4c6d.firebasestorage.app`)
- `FIREBASE_PROJECT_ID`: Override project ID
- `FIREBASE_CLIENT_EMAIL`: Override client email
- `FIREBASE_PRIVATE_KEY`: Override private key
- `MODEL_NAME`: HuggingFace model name (default: `maya-research/maya1`)

## Firebase Integration

The endpoint can upload generated audio directly to Firebase Storage:

- **Path format**: `users/{userId}/tts/tts_{timestamp}_{sanitized_text}.wav`
- **Public URLs**: Audio files are made publicly accessible
- **Fallback**: If upload fails, audio_base64 is still returned

## Voice Description Examples

```
"Female, in her 30s with an American accent, energetic, clear diction"
"Male, late 20s, neutral American, warm baritone, calm pacing"
"Dark villain character, Male voice in their 40s with a British accent, low pitch, gravelly timbre, slow pacing, angry tone at high intensity"
"Mythical godlike magical character, Female voice in their 30s, slow pacing, curious tone at medium intensity"
```

## Dependencies

- `torch>=2.0.0` (CUDA-enabled)
- `transformers>=4.40.0`
- `snac` (SNAC neural codec)
- `soundfile>=0.12.0`
- `firebase-admin>=6.0.0`
- `runpod>=1.0.0`

## Troubleshooting

### Model Loading Issues

- Ensure GPU is available and CUDA is properly configured
- Check that model can be downloaded from HuggingFace
- Verify sufficient VRAM (16GB+)

### Firebase Upload Failures

- Verify `FIREBASE_SERVICE_ACCOUNT_KEY` is valid JSON
- Check Firebase Storage bucket permissions
- Ensure service account has Storage Admin role

### Audio Generation Errors

- Check that text input is not empty
- Verify voice description is reasonable
- Reduce `max_new_tokens` if generation times out

## License

Apache 2.0 (same as Maya1 model)

## References

- [Maya1 Model Card](https://huggingface.co/maya-research/maya1)
- [RunPod Documentation](https://docs.runpod.io/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)

