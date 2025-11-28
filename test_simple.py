#!/usr/bin/env python3
"""
Simple test script for Maya1 RunPod Endpoint
Quick test with a single request
"""

import requests
import json
import base64

# RunPod Configuration
RUNPOD_API_KEY = "rpa_C55TBQG7H6FM7G3Q7A6JM7ZJCDKA3I2J3EO0TAH8fxyddo"
ENDPOINT_URL = "https://api.runpod.ai/v2/o10i3yz4aaajfc/run"

def test_endpoint():
    """Simple endpoint test."""
    import time
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "text": "Hello everyone! <laugh> Welcome to this comprehensive test of the Maya1 text-to-speech system. <excited> We are going to test a really long passage of text with multiple emotion tags to ensure that the system can handle extended content without cutting off.",
            "voice_description": "Female voice, American accent, clear and professional",
            # MOST CONSISTENT PARAMETERS:
            "temperature": 0.8,  # Higher temperature for better emotion tag expressiveness
            "max_new_tokens": 2000,  # Let auto-scaling handle it (500 + 10*words formula) - most reliable
            "upload_to_firebase": False
        }
    }
    
    print("Testing Maya1 RunPod Endpoint")
    print("=" * 50)
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"Request payload:")
    print(json.dumps(payload, indent=2))
    print("\nSending async request...")
    
    try:
        # Step 1: Submit job
        response = requests.post(
            ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        job_data = response.json()
        
        job_id = job_data.get('id')
        if not job_id:
            print(f"\n❌ No job ID in response: {job_data}")
            return False
        
        print(f"✅ Job submitted: {job_id}")
        print(f"   Status: {job_data.get('status', 'UNKNOWN')}")
        
        # Step 2: Poll for completion
        # Extract base URL (remove /run from end if present)
        base_url = ENDPOINT_URL.rstrip('/run').rstrip('/')
        status_url = f"{base_url}/status/{job_id}"
        print(f"\nPolling for completion...")
        print(f"Status URL: {status_url}")
        
        max_wait = 300  # 5 minutes
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
                print("=" * 50)
                
                # Extract nested output structure
                output = result.get('output', {})
                if isinstance(output, dict) and 'output' in output:
                    output = output['output']
                
                print(f"   Sampling rate: {output.get('sampling_rate')} Hz")
                print(f"   Duration: {output.get('duration')} seconds")
                print(f"   Format: {output.get('format')}")
                
                audio_base64 = output.get('audio_base64', '')
                if audio_base64:
                    # Save audio file
                    audio_bytes = base64.b64decode(audio_base64)
                    output_file = 'test_output.wav'
                    with open(output_file, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"   ✅ Audio saved to: {output_file}")
                    print(f"   Audio size: {len(audio_bytes) / 1024:.2f} KB")
                else:
                    print(f"   ⚠️  No audio data in response")
                
                if 'firebase_url' in output:
                    print(f"   Firebase URL: {output['firebase_url']}")
                
                return True
            
            elif status == 'FAILED':
                print(f"\n❌ Job failed")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                if 'output' in result and isinstance(result['output'], dict):
                    if 'error' in result['output']:
                        print(f"   Output Error: {result['output']['error']}")
                return False
            
            time.sleep(2)
        
        print(f"\n❌ Timeout: Job did not complete within {max_wait} seconds")
        return False
    
    except requests.exceptions.Timeout:
        print("\n❌ Request timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_endpoint()
    sys.exit(0 if success else 1)

