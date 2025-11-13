#!/usr/bin/env python3
import requests

# Quick test
def test_apis():
    print("🔍 Quick API Test")
    
    # Test Faceit
    try:
        r = requests.get("https://open.faceit.com/data/v4/players?nickname=device", 
                        headers={"Authorization": "Bearer abf395a0-9eb2-4ff6-9697-da3079bc3567"})
        print(f"Faceit: {r.status_code}")
    except:
        print("Faceit: Error")
    
    # Test our API
    try:
        r = requests.get("https://pattmsc.online/api/health")
        print(f"Our API: {r.status_code}")
    except:
        print("Our API: Error")

if __name__ == "__main__":
    test_apis()
