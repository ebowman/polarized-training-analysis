#!/usr/bin/env python
"""
Test script for the generate-config API endpoint
"""

import requests
import json
import sys

def test_generate_config_endpoint():
    """Test the /api/settings/generate-config endpoint"""
    base_url = "http://localhost:5002"  # Adjust if using different port
    
    print("Testing /api/settings/generate-config endpoint...")
    
    # Test 1: Generate config from example preferences text
    test_preferences = """
# My Workout Preferences

## Sports
- Cycling (Indoor on Peloton, Outdoor road cycling)
- Running (Treadmill and outdoor)
- Rowing (Concept2 ergometer)

## Thresholds
- FTP: 301 watts
- LTHR: 165 bpm
- Max Heart Rate: 185 bpm

## Training Philosophy
I follow a polarized training approach, spending about 80% of my time in easy zones
and 20% in harder efforts. I typically train 8-10 hours per week.

## Equipment
- Peloton bike for indoor cycling
- Concept2 rower
- Garmin watch for running
"""
    
    # Test with preferences text
    print("\n1. Testing with preferences text...")
    response = requests.post(
        f"{base_url}/api/settings/generate-config",
        json={"preferences_text": test_preferences},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print("✅ Success! Generated config:")
            print(f"   - Detected sports: {data['detected_sports']}")
            print(f"   - Philosophy: {data['config']['user_profile']['philosophy']}")
            print(f"   - FTP: {data['config']['user_profile']['thresholds'].get('ftp', 'Not set')}")
            print(f"   - LTHR: {data['config']['user_profile']['thresholds'].get('lthr', 'Not set')}")
            
            # Save generated config for inspection
            with open("test_generated_config.json", "w") as f:
                json.dump(data['config'], f, indent=2)
            print("\n   Generated config saved to test_generated_config.json")
        else:
            print(f"❌ Failed: {data['error']}")
    else:
        print(f"❌ HTTP Error {response.status_code}: {response.text}")
    
    # Test 2: Generate config from file (if exists)
    print("\n2. Testing with preferences file...")
    response = requests.post(
        f"{base_url}/api/settings/generate-config",
        json={},  # Empty body - should load from file
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print("✅ Success! Loaded from preferences file")
            print(f"   - Detected sports: {data['detected_sports']}")
        else:
            print(f"⚠️  No preferences file found: {data['error']}")
    else:
        print(f"❌ HTTP Error {response.status_code}: {response.text}")
    
    # Test 3: Test error handling (no API key)
    print("\n3. Testing error handling...")
    # This would fail if no API keys are configured
    # The actual test depends on your environment setup

if __name__ == "__main__":
    try:
        test_generate_config_endpoint()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the Flask app is running on port 5002")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)