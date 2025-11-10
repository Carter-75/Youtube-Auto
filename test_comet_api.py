"""
EXHAUSTIVE CometAPI Suno Endpoint Test & Debug Script
Tests all possible endpoint combinations, parameter variations, and API structures
"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv('COMET_API_KEY')
print("="*80)
print("EXHAUSTIVE CometAPI Suno Endpoint Debugger")
print("="*80)
print(f"API Key (first 15 chars): {api_key[:15]}...")
print(f"API Key length: {len(api_key) if api_key else 0} characters")

# Base payload
base_payload = {
    "prompt": "Lofi study music",
    "tags": "lofi, chill",
    "title": "Test Track",
    "make_instrumental": True,
    "wait_audio": False
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# EXHAUSTIVE endpoint combinations (all possible variations)
test_cases = [
    # Standard v1 patterns
    ("https://api.cometapi.com", "/v1/suno/generate"),
    ("https://api.cometapi.com", "/v1/suno/custom_generate"),
    ("https://api.cometapi.com", "/v1/suno/submit/music"),
    ("https://api.cometapi.com", "/v1/suno/music"),
    ("https://api.cometapi.com", "/v1/suno/create"),
    ("https://api.cometapi.com", "/v1/suno/music/generate"),
    
    # Base URL with /v1 patterns
    ("https://api.cometapi.com/v1", "/suno/generate"),
    ("https://api.cometapi.com/v1", "/suno/custom_generate"),
    ("https://api.cometapi.com/v1", "/suno/create"),
    ("https://api.cometapi.com/v1", "/suno/music"),
    
    # API prefix patterns
    ("https://api.cometapi.com", "/api/suno/generate"),
    ("https://api.cometapi.com", "/api/suno/custom_generate"),
    ("https://api.cometapi.com", "/api/v1/suno/generate"),
    ("https://api.cometapi.com", "/api/custom_generate"),
    
    # Suno first patterns
    ("https://api.cometapi.com", "/suno/generate"),
    ("https://api.cometapi.com", "/suno/custom_generate"),
    ("https://api.cometapi.com", "/suno/v1/generate"),
    ("https://api.cometapi.com", "/suno/create"),
    
    # Alternative structures
    ("https://api.cometapi.com", "/v1/music/suno/generate"),
    ("https://api.cometapi.com", "/v1/generate/suno"),
    ("https://api.cometapi.com", "/generate/suno"),
]

print(f"\n{'='*80}")
print(f"PHASE 1: Testing {len(test_cases)} endpoint combinations")
print(f"{'='*80}\n")

working_endpoint = None

for i, (base_url, endpoint) in enumerate(test_cases, 1):
    full_url = f"{base_url}{endpoint}"
    print(f"[{i}/{len(test_cases)}] Testing: {full_url}")
    
    try:
        response = requests.post(full_url, headers=headers, json=base_payload, timeout=30)
        
        if response.status_code == 200:
            try:
                json_resp = response.json()
                print(f"  ✅✅✅ SUCCESS! Status: {response.status_code}")
                print(f"  Response keys: {list(json_resp.keys())}")
                print(f"  Full response:\n{json.dumps(json_resp, indent=2)}")
                working_endpoint = full_url
                print(f"\n{'='*80}")
                print(f"🎉 FOUND WORKING ENDPOINT: {full_url}")
                print(f"{'='*80}\n")
                break
            except:
                if '<html' in response.text.lower() or '<!doctype' in response.text.lower():
                    print(f"  ❌ Returned HTML webpage, not JSON API")
                else:
                    print(f"  ⚠️  Status 200 but non-JSON response")
                    print(f"  Response preview: {response.text[:150]}")
        elif response.status_code == 401:
            print(f"  ❌ 401 Unauthorized - API key may be invalid")
        elif response.status_code == 403:
            print(f"  ❌ 403 Forbidden - Access denied")
        elif response.status_code == 404:
            print(f"  ❌ 404 Not Found")
        elif response.status_code == 400:
            print(f"  ⚠️  400 Bad Request (endpoint exists but params wrong?)")
            print(f"  Response: {response.text[:150]}")
        else:
            print(f"  ⚠️  Status {response.status_code}")
            print(f"  Response: {response.text[:150]}")
    except requests.exceptions.Timeout:
        print(f"  ❌ Request timeout")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    print()

# PHASE 2: If no endpoint found, test with parameter variations
if not working_endpoint:
    print(f"{'='*80}")
    print("PHASE 2: Testing parameter variations on most promising endpoints")
    print(f"{'='*80}\n")
    
    # Try different parameter combinations
    param_variations = [
        {"prompt": "test", "make_instrumental": True},
        {"prompt": "test"},
        {"gpt_description_prompt": "Lofi study music", "make_instrumental": True},
        {"custom_prompt": "Lofi study music", "tags": "lofi"},
    ]
    
    promising_endpoints = [
        "https://api.cometapi.com/v1/suno/generate",
        "https://api.cometapi.com/v1/suno/custom_generate",
    ]
    
    for endpoint in promising_endpoints:
        for params in param_variations:
            print(f"Testing {endpoint}")
            print(f"  With params: {params}")
            try:
                response = requests.post(endpoint, headers=headers, json=params, timeout=30)
                if response.status_code in [200, 400]:
                    print(f"  Status {response.status_code}: {response.text[:200]}")
                    if response.status_code == 200:
                        working_endpoint = endpoint
                        break
            except:
                pass
            print()
        if working_endpoint:
            break

# PHASE 3: Test GET requests (in case it's not POST)
if not working_endpoint:
    print(f"{'='*80}")
    print("PHASE 3: Testing GET requests (in case API uses GET instead of POST)")
    print(f"{'='*80}\n")
    
    for base_url, endpoint in test_cases[:5]:
        full_url = f"{base_url}{endpoint}"
        try:
            response = requests.get(full_url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ GET {full_url} - Status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except:
            pass

print("\n" + "="*80)
if working_endpoint:
    print("✅ SUCCESS! Working endpoint found above.")
else:
    print("❌ NO WORKING ENDPOINT FOUND")
    print("\nRECOMMENDATIONS:")
    print("1. Log into https://cometapi.com/dashboard")
    print("2. Navigate to 'API Documentation' or 'API Docs' section")
    print("3. Find the Suno API section and copy the EXACT endpoint URL")
    print("4. Check if your API key has Suno API access enabled")
    print("5. Verify your account has credits/balance")
print("="*80)

