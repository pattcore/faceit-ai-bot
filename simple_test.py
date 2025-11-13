#!/usr/bin/env python3
"""
Simple test without external dependencies
"""
import urllib.request
import json

def test_apis():
    """Test APIs using only standard library"""
    print("🚀 Testing APIs...")
    
    # Test our health endpoint
    try:
        with urllib.request.urlopen("https://pattmsc.online/api/health") as response:
            data = json.loads(response.read())
            print(f"✅ Our API: {data}")
    except Exception as e:
        print(f"❌ Our API error: {e}")
    
    # Test Faceit API
    try:
        req = urllib.request.Request(
            "https://open.faceit.com/data/v4/players?nickname=device",
            headers={"Authorization": "Bearer abf395a0-9eb2-4ff6-9697-da3079bc3567"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            print(f"✅ Faceit API: Found {data.get('nickname')} with ELO {data.get('games', {}).get('cs2', {}).get('faceit_elo')}")
    except Exception as e:
        print(f"❌ Faceit API error: {e}")

if __name__ == "__main__":
    test_apis()
