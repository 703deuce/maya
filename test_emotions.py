#!/usr/bin/env python3
"""
Test Maya1 endpoint with emotion tags and longer text
"""

import requests
import json
import base64
import time

RUNPOD_API_KEY = "rpa_C55TBQG7H6FM7G3Q7A6JM7ZJCDKA3I2J3EO0TAH8fxyddo"
ENDPOINT_URL = "https://api.runpod.ai/v2/o10i3yz4aaajfc/run"

def test_with_emotions():
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "text": "Welcome to our podcast! <laugh> Today we have an absolutely amazing guest. <gasp> This is incredible! We're going to have so much fun exploring this fascinating topic together. <laugh_harder> I can't wait to share this with all of you listening at home.",
            "voice_description": "Female, in her 30s with an American accent, energetic, clear diction, enthusiastic",
            "temperature": 0.7,
            "max_new_tokens": 1500,
            "upload_to_firebase": False
        }
    }
    
    print("Testing Maya1 with Emotion Tags")
    print("=" * 60)
    print(f"Text: {payload['input']['text']}")
    print(f"\nSending request...")
    
    try:
        # Submit job
        response = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get('id')
        
        print(f"✅ Job submitted: {job_id}")
        
        # Poll for completion
        base_url = ENDPOINT_URL.rstrip('/run').rstrip('/')
        status_url = f"{base_url}/status/{job_id}"
        
        max_wait = 300
        start_time = time.time()
        poll_count = 0
        
        while time.time() - start_time < max_wait:
            poll_count += 1
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_response.raise_for_status()
            result = status_response.json()
            
            status = result.get('status', 'UNKNOWN')
            
            if poll_count == 1 or poll_count % 10 == 0:
                print(f"   [{poll_count}] Status: {status}")
            
            if status == 'COMPLETED':
                print(f"\n✅ Job completed!")
                print("=" * 60)
                
                output = result.get('output', {})
                if isinstance(output, dict) and 'output' in output:
                    output = output['output']
                
                print(f"   Sampling rate: {output.get('sampling_rate')} Hz")
                print(f"   Duration: {output.get('duration')} seconds")
                print(f"   Format: {output.get('format')}")
                
                audio_base64 = output.get('audio_base64', '')
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    output_file = 'test_emotions.wav'
                    with open(output_file, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"   ✅ Audio saved to: {output_file}")
                    print(f"   Audio size: {len(audio_bytes) / 1024:.2f} KB")
                    print(f"\n✅ Success! Audio generated with emotion tags.")
                    return True
                else:
                    print(f"   ⚠️  No audio data in response")
                    return False
            
            elif status == 'FAILED':
                print(f"\n❌ Job failed")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                if 'output' in result and isinstance(result['output'], dict):
                    if 'error' in result['output']:
                        print(f"   Output Error: {result['output']['error']}")
                return False
            
            time.sleep(2)
        
        print(f"\n❌ Timeout")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_emotions()

