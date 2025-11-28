#!/usr/bin/env python3
"""
Test Maya1 endpoint with very long text to ensure complete generation
"""

import requests
import json
import base64
import time

RUNPOD_API_KEY = "rpa_C55TBQG7H6FM7G3Q7A6JM7ZJCDKA3I2J3EO0TAH8fxyddo"
ENDPOINT_URL = "https://api.runpod.ai/v2/o10i3yz4aaajfc/run"

def test_long_text():
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "text": "The quick brown fox jumps over the lazy dog. This is a test to ensure that the Maya1 text-to-speech system can handle longer passages of text without cutting off prematurely. We want to make sure that all the words are spoken clearly and the audio completes naturally. The system should generate smooth, natural speech that flows well from beginning to end. This is important for production use cases where we need reliable and complete audio generation.",
            "voice_description": "Male, late 20s, neutral American accent, warm baritone, calm pacing",
            "temperature": 0.7,
            "max_new_tokens": 2000,
            "upload_to_firebase": False
        }
    }
    
    print("Testing Maya1 with Long Text")
    print("=" * 60)
    print(f"Text length: {len(payload['input']['text'])} characters")
    print(f"Max tokens: {payload['input']['max_new_tokens']}")
    print(f"\nSending request...")
    
    try:
        response = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get('id')
        
        print(f"✅ Job submitted: {job_id}")
        
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
                
                sampling_rate = output.get('sampling_rate')
                duration = output.get('duration')
                format_type = output.get('format')
                
                print(f"   Sampling rate: {sampling_rate} Hz")
                print(f"   Duration: {duration} seconds")
                print(f"   Format: {format_type}")
                
                audio_base64 = output.get('audio_base64', '')
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    output_file = 'test_long.wav'
                    with open(output_file, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"   ✅ Audio saved to: {output_file}")
                    print(f"   Audio size: {len(audio_bytes) / 1024:.2f} KB")
                    print(f"   Expected duration: ~{len(payload['input']['text']) / 15:.1f} seconds (rough estimate)")
                    print(f"   Actual duration: {duration} seconds")
                    return True
                else:
                    print(f"   ⚠️  No audio data")
                    return False
            
            elif status == 'FAILED':
                print(f"\n❌ Job failed")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
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
    test_long_text()

