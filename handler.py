#!/usr/bin/env python3
"""
RunPod Serverless Handler for Maya1 TTS Model
Generates expressive voice audio from text and voice descriptions
"""

import os
import json
import base64
import io
from datetime import datetime
from typing import Dict, Any, Optional

import torch
import numpy as np
import soundfile as sf
from transformers import AutoModelForCausalLM, AutoTokenizer
from snac import SNAC

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, storage, exceptions as firebase_exceptions
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# Maya1 Special Tokens
CODE_START_TOKEN_ID = 128257
CODE_END_TOKEN_ID = 128258
CODE_TOKEN_OFFSET = 128266
SNAC_MIN_ID = 128266
SNAC_MAX_ID = 156937
SNAC_TOKENS_PER_FRAME = 7

SOH_ID = 128259  # Start of Header
EOH_ID = 128260  # End of Header
SOA_ID = 128261  # Start of Audio
BOS_ID = 128000  # Beginning of Sequence
TEXT_EOT_ID = 128009  # End of Text

# Global model and tokenizer (loaded once at startup)
model = None
tokenizer = None
snac_decoder = None
firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK from environment variables."""
    global firebase_app
    
    if not FIREBASE_AVAILABLE:
        return None
    
    if firebase_app is not None:
        return firebase_app
    
    try:
        # Check if already initialized
        if firebase_admin._apps:
            firebase_app = firebase_admin.get_app()
            return firebase_app
        
        # Try service account JSON first
        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
        if service_account_json:
            try:
                cred_dict = json.loads(service_account_json)
                cred = credentials.Certificate(cred_dict)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing FIREBASE_SERVICE_ACCOUNT_KEY: {e}")
                return None
        else:
            # Try individual environment variables
            project_id = os.getenv('FIREBASE_PROJECT_ID')
            client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
            private_key = os.getenv('FIREBASE_PRIVATE_KEY')
            
            if not all([project_id, client_email, private_key]):
                print("Firebase credentials not found in environment variables")
                return None
            
            cred = credentials.Certificate({
                "project_id": project_id,
                "client_email": client_email,
                "private_key": private_key.replace('\\n', '\n'),
            })
        
        # Get storage bucket from env or use default
        storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET', 'aitts-d4c6d.firebasestorage.app')
        
        firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket
        })
        
        print("Firebase initialized successfully")
        return firebase_app
    
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        return None


def load_model():
    """Load Maya1 model and tokenizer (called once at startup)."""
    global model, tokenizer, snac_decoder
    
    if model is not None and tokenizer is not None:
        return model, tokenizer
    
    model_name = os.getenv('MODEL_NAME', 'maya-research/maya1')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"Loading model {model_name} on {device}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16 if device == 'cuda' else torch.float32,
        device_map='auto' if device == 'cuda' else None
    )
    
    if device == 'cpu':
        model = model.to(device)
    
    model.eval()
    
    # Initialize SNAC decoder
    snac_decoder = SNAC()
    
    print("Model loaded successfully")
    return model, tokenizer


def build_prompt(description: str, text: str) -> str:
    """Build formatted prompt for Maya1."""
    soh_token = tokenizer.decode([SOH_ID])
    eoh_token = tokenizer.decode([EOH_ID])
    soa_token = tokenizer.decode([SOA_ID])
    sos_token = tokenizer.decode([CODE_START_TOKEN_ID])
    eot_token = tokenizer.decode([TEXT_EOT_ID])
    bos_token = tokenizer.bos_token if tokenizer.bos_token else tokenizer.decode([BOS_ID])
    
    formatted_text = f'<description="{description}"> {text}'
    
    prompt = (
        soh_token + bos_token + formatted_text + eot_token +
        eoh_token + soa_token + sos_token
    )
    
    return prompt


def extract_snac_codes(token_ids: list) -> list:
    """Extract SNAC codes from generated tokens."""
    try:
        eos_idx = token_ids.index(CODE_END_TOKEN_ID)
    except ValueError:
        eos_idx = len(token_ids)
    
    snac_codes = [
        token_id for token_id in token_ids[:eos_idx]
        if SNAC_MIN_ID <= token_id <= SNAC_MAX_ID
    ]
    
    return snac_codes


def unpack_snac_from_7(snac_tokens: list) -> tuple:
    """Unpack 7-token SNAC frames to 3 hierarchical levels."""
    if snac_tokens and snac_tokens[-1] == CODE_END_TOKEN_ID:
        snac_tokens = snac_tokens[:-1]
    
    frames = len(snac_tokens) // SNAC_TOKENS_PER_FRAME
    snac_tokens = snac_tokens[:frames * SNAC_TOKENS_PER_FRAME]
    
    if frames == 0:
        return ([], [], [])
    
    l1, l2, l3 = [], [], []
    
    for i in range(frames):
        slots = snac_tokens[i*7:(i+1)*7]
        l1.append((slots[0] - CODE_TOKEN_OFFSET) % 4096)
        l2.extend([
            (slots[1] - CODE_TOKEN_OFFSET) % 4096,
            (slots[4] - CODE_TOKEN_OFFSET) % 4096,
        ])
        l3.extend([
            (slots[2] - CODE_TOKEN_OFFSET) % 4096,
            (slots[3] - CODE_TOKEN_OFFSET) % 4096,
            (slots[5] - CODE_TOKEN_OFFSET) % 4096,
            (slots[6] - CODE_TOKEN_OFFSET) % 4096,
        ])
    
    return (l1, l2, l3)


def generate_audio(text: str, voice_description: str, temperature: float = 0.7, max_new_tokens: int = 2000) -> tuple:
    """
    Generate audio from text and voice description.
    
    Returns:
        tuple: (audio_array, sampling_rate)
    """
    global model, tokenizer, snac_decoder
    
    if model is None or tokenizer is None:
        load_model()
    
    # Build prompt
    prompt = build_prompt(voice_description, text)
    
    # Tokenize input
    input_ids = tokenizer.encode(prompt, return_tensors='pt')
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)
    
    # Generate tokens
    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    # Extract generated tokens (remove input tokens)
    generated_tokens = outputs[0][input_ids.shape[1]:].cpu().tolist()
    
    # Extract SNAC codes
    snac_codes = extract_snac_codes(generated_tokens)
    
    if not snac_codes:
        raise ValueError("No SNAC codes generated. Model may not have produced valid audio tokens.")
    
    # Unpack SNAC tokens
    l1, l2, l3 = unpack_snac_from_7(snac_codes)
    
    # Decode SNAC to audio
    # SNAC.decode() expects a single tuple/list argument containing (l1, l2, l3)
    audio_array = snac_decoder.decode((l1, l2, l3))
    sampling_rate = 24000  # Maya1 uses 24kHz
    
    return audio_array, sampling_rate


def audio_to_base64(audio_array: np.ndarray, sampling_rate: int) -> str:
    """Convert audio array to base64-encoded WAV string."""
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, sampling_rate, format='WAV')
    buffer.seek(0)
    audio_bytes = buffer.read()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    return audio_base64


def upload_to_firebase(audio_base64: str, user_id: str, text_preview: str) -> Dict[str, Any]:
    """
    Upload generated audio directly to Firebase Storage.
    
    Returns:
        dict with success, url, filename, storage_path keys
    """
    if not FIREBASE_AVAILABLE:
        return {
            "success": False,
            "error": "Firebase Admin SDK not available"
        }
    
    firebase_app = init_firebase()
    if firebase_app is None:
        return {
            "success": False,
            "error": "Firebase not initialized"
        }
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Generate filename
        timestamp = int(datetime.now().timestamp() * 1000)
        sanitized_text = "".join(c for c in text_preview[:30] if c.isalnum() or c == ' ').strip().replace(' ', '_')
        filename = f"tts_{timestamp}_{sanitized_text}.wav"
        
        # Storage path
        storage_path = f"users/{user_id}/tts/{filename}"
        
        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(storage_path)
        blob.upload_from_string(audio_bytes, content_type='audio/wav')
        
        # Make publicly accessible
        blob.make_public()
        url = blob.public_url
        
        return {
            "success": True,
            "url": url,
            "filename": filename,
            "storage_path": storage_path
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler function.
    
    Expected input:
    {
        "input": {
            "text": "Hello world <laugh> this is great!",
            "voice_description": "Female, in her 30s with an American accent, energetic",
            "temperature": 0.7,
            "max_new_tokens": 2000,
            "upload_to_firebase": true,
            "firebase_user_id": "user123"
        }
    }
    """
    try:
        # Load model if not already loaded
        if model is None:
            load_model()
        
        # Extract input
        input_data = event.get('input', {})
        text = input_data.get('text', '')
        voice_description = input_data.get('voice_description', 'Neutral voice, clear speech')
        temperature = float(input_data.get('temperature', 0.7))
        max_new_tokens = int(input_data.get('max_new_tokens', 2000))
        upload_to_firebase_flag = input_data.get('upload_to_firebase', False)
        firebase_user_id = input_data.get('firebase_user_id', '')
        
        # Validate input
        if not text:
            return {
                "error": "Text input is required",
                "status": "FAILED"
            }
        
        if upload_to_firebase_flag and not firebase_user_id:
            return {
                "error": "firebase_user_id is required when upload_to_firebase is true",
                "status": "FAILED"
            }
        
        # Generate audio
        audio_array, sampling_rate = generate_audio(
            text=text,
            voice_description=voice_description,
            temperature=temperature,
            max_new_tokens=max_new_tokens
        )
        
        # Calculate duration
        duration = len(audio_array) / sampling_rate
        
        # Convert to base64
        audio_base64 = audio_to_base64(audio_array, sampling_rate)
        
        # Build response
        response = {
            "audio_base64": audio_base64,
            "sampling_rate": sampling_rate,
            "duration": round(duration, 2),
            "format": "wav",
            "content_type": "audio/wav"
        }
        
        # Upload to Firebase if requested
        if upload_to_firebase_flag:
            firebase_result = upload_to_firebase(
                audio_base64=audio_base64,
                user_id=firebase_user_id,
                text_preview=text[:30]
            )
            
            if firebase_result.get("success"):
                response["firebase_url"] = firebase_result["url"]
                response["firebase_path"] = firebase_result["storage_path"]
                response["firebase_filename"] = firebase_result["filename"]
            else:
                response["firebase_upload_error"] = firebase_result.get("error", "Unknown error")
        
        return {
            "id": event.get("id", "unknown"),
            "status": "COMPLETED",
            "output": response
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error in handler: {error_msg}")
        import traceback
        traceback.print_exc()
        
        return {
            "id": event.get("id", "unknown"),
            "status": "FAILED",
            "error": error_msg
        }


# RunPod serverless entry point
if __name__ == "__main__":
    import runpod
    
    # Load model at startup
    load_model()
    
    # Initialize Firebase if credentials are available
    init_firebase()
    
    # Start RunPod serverless worker
    runpod.serverless.start({"handler": handler})

