#!/usr/bin/env python3
"""
Test script for Maya1 RunPod Serverless Endpoint
Tests the endpoint with various voice descriptions and emotion tags
"""

import requests
import json
import base64
import sys
import time
from pathlib import Path

# RunPod Configuration
RUNPOD_API_KEY = "rpa_C55TBQG7H6FM7G3Q7A6JM7ZJCDKA3I2J3EO0TAH8fxyddo"
ENDPOINT_URL = "https://api.runpod.ai/v2/o10i3yz4aaajfc/run"

# Test cases
TEST_CASES = [
    {
        "name": "Basic Test - Neutral Voice",
        "input": {
            "text": "Hello, this is a test of the Maya1 text-to-speech system.",
            "voice_description": "Neutral voice, clear speech, American accent",
            "temperature": 0.7,
            "max_new_tokens": 500,
            "upload_to_firebase": False
        }
    },
    {
        "name": "Emotion Tags Test",
        "input": {
            "text": "Welcome to our podcast! <laugh> Today we have an amazing guest. <gasp> This is incredible!",
            "voice_description": "Female, in her 30s with an American accent, energetic, clear diction",
            "temperature": 0.7,
            "max_new_tokens": 800,
            "upload_to_firebase": False
        }
    },
    {
        "name": "Character Voice Test",
        "input": {
            "text": "You dare challenge me, mortal <snort> how amusing. Your kind always thinks they can win.",
            "voice_description": "Demon character, Male voice in their 30s with a Middle Eastern accent, screaming tone at high intensity",
            "temperature": 0.8,
            "max_new_tokens": 1000,
            "upload_to_firebase": False
        }
    },
    {
        "name": "Firebase Upload Test",
        "input": {
            "text": "This audio will be uploaded to Firebase Storage.",
            "voice_description": "Male, late 20s, neutral American, warm baritone, calm pacing",
            "temperature": 0.7,
            "max_new_tokens": 500,
            "upload_to_firebase": True,
            "firebase_user_id": "test_user_123"
        }
    }
]


def send_request(test_case, sync=True):
    """Send a request to the RunPod endpoint."""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": test_case["input"]
    }
    
    endpoint = f"{ENDPOINT_URL}sync" if sync else f"{ENDPOINT_URL}"
    
    print(f"\n{'='*60}")
    print(f"Test: {test_case['name']}")
    print(f"{'='*60}")
    print(f"Endpoint: {endpoint}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"\nSending request...")
    
    try:
        if sync:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        else:
            # Async request
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data.get("id")
            print(f"Job ID: {job_id}")
            
            # Poll for completion
            # Extract base URL (remove /run from end if present)
            base_url = endpoint.rstrip('/run').rstrip('/')
            status_url = f"{base_url}/status/{job_id}"
            max_wait = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(status_url, headers=headers, timeout=30)
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data.get("status")
                print(f"Status: {status}")
                
                if status == "COMPLETED":
                    return status_data
                elif status == "FAILED":
                    error = status_data.get("error", "Unknown error")
                    print(f"Job failed: {error}")
                    return status_data
                
                time.sleep(2)
            
            print("Timeout waiting for job completion")
            return {"status": "TIMEOUT", "error": "Job did not complete in time"}
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return {"error": str(e), "status": "FAILED"}


def save_audio(base64_audio, filename):
    """Save base64-encoded audio to file."""
    try:
        audio_bytes = base64.b64decode(base64_audio)
        output_path = Path("test_output")
        output_path.mkdir(exist_ok=True)
        
        filepath = output_path / filename
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        
        print(f"Audio saved to: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"Error saving audio: {e}")
        return None


def validate_response(response, test_case):
    """Validate the response structure and content."""
    print(f"\n{'─'*60}")
    print("Response Validation")
    print(f"{'─'*60}")
    
    if "error" in response:
        print(f"❌ Error in response: {response['error']}")
        return False
    
    status = response.get("status")
    print(f"Status: {status}")
    
    if status != "COMPLETED":
        print(f"❌ Expected COMPLETED, got {status}")
        return False
    
    output = response.get("output", {})
    
    # Check required fields
    required_fields = ["audio_base64", "sampling_rate", "duration", "format", "content_type"]
    missing_fields = [field for field in required_fields if field not in output]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    print(f"✅ All required fields present")
    print(f"   - Sampling rate: {output['sampling_rate']} Hz")
    print(f"   - Duration: {output['duration']} seconds")
    print(f"   - Format: {output['format']}")
    print(f"   - Content type: {output['content_type']}")
    
    # Check audio data
    audio_base64 = output.get("audio_base64", "")
    if not audio_base64:
        print(f"❌ No audio data in response")
        return False
    
    audio_size = len(audio_base64) * 3 / 4  # Approximate base64 to bytes
    print(f"   - Audio size: ~{audio_size / 1024:.2f} KB")
    
    # Check Firebase upload if requested
    if test_case["input"].get("upload_to_firebase"):
        if "firebase_url" in output:
            print(f"✅ Firebase upload successful")
            print(f"   - URL: {output['firebase_url']}")
            print(f"   - Path: {output.get('firebase_path', 'N/A')}")
        else:
            error = output.get("firebase_upload_error", "Unknown error")
            print(f"⚠️  Firebase upload failed: {error}")
    
    return True


def run_tests():
    """Run all test cases."""
    print("="*60)
    print("Maya1 RunPod Endpoint Test Suite")
    print("="*60)
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"API Key: {RUNPOD_API_KEY[:20]}...")
    print(f"Total tests: {len(TEST_CASES)}")
    
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n\n[{i}/{len(TEST_CASES)}]")
        
        # Try sync endpoint first, fallback to async
        response = send_request(test_case, sync=True)
        
        if "error" in response and "timeout" in str(response.get("error", "")).lower():
            print("Sync timeout, trying async endpoint...")
            response = send_request(test_case, sync=False)
        
        # Validate response
        is_valid = validate_response(response, test_case)
        
        # Save audio if valid
        if is_valid and "output" in response:
            output = response["output"]
            audio_base64 = output.get("audio_base64")
            if audio_base64:
                filename = f"test_{i}_{test_case['name'].lower().replace(' ', '_')}.wav"
                save_audio(audio_base64, filename)
        
        results.append({
            "test": test_case["name"],
            "passed": is_valid,
            "status": response.get("status", "UNKNOWN")
        })
        
        # Brief pause between tests
        time.sleep(1)
    
    # Summary
    print("\n\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    for result in results:
        status_icon = "✅" if result["passed"] else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

