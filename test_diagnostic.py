#!/usr/bin/env python3
"""
Diagnostic test for RunPod endpoint
Checks endpoint status and provides detailed information
"""

import requests
import json

RUNPOD_API_KEY = "rpa_C55TBQG7H6FM7G3Q7A6JM7ZJCDKA3I2J3EO0TAH8fxyddo"
ENDPOINT_URL = "https://api.runpod.ai/v2/o10i3yz4aaajfc/run"

def check_endpoint_health():
    """Check if the endpoint is responding."""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("RunPod Endpoint Diagnostic")
    print("=" * 60)
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"API Key: {RUNPOD_API_KEY[:20]}...")
    print()
    
    # Test 1: Submit a minimal job
    print("Test 1: Submitting minimal test job...")
    payload = {
        "input": {
            "text": "test",
            "voice_description": "neutral voice"
        }
    }
    
    try:
        response = requests.post(
            ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Endpoint is accepting requests")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            job_id = result.get('id')
            if job_id:
                print(f"\nTest 2: Checking job status...")
                base_url = ENDPOINT_URL.rstrip('/run').rstrip('/')
                status_url = f"{base_url}/status/{job_id}"
                
                status_response = requests.get(status_url, headers=headers, timeout=30)
                print(f"   Status URL: {status_url}")
                print(f"   Status Code: {status_response.status_code}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   ✅ Status endpoint working")
                    print(f"   Status Data: {json.dumps(status_data, indent=2)}")
                    
                    status = status_data.get('status')
                    if status == 'IN_QUEUE':
                        print(f"\n   ⚠️  Job is in queue. Possible reasons:")
                        print(f"      - Endpoint is cold-starting (first request)")
                        print(f"      - No workers available")
                        print(f"      - Handler is failing to start")
                        print(f"      - Docker image not built/deployed")
                    
                    return True
                else:
                    print(f"   ❌ Status endpoint failed: {status_response.text}")
                    return False
            else:
                print(f"   ⚠️  No job ID in response")
                return False
        else:
            print(f"   ❌ Endpoint returned error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

if __name__ == "__main__":
    check_endpoint_health()

