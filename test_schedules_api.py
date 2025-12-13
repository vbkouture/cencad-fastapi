
import sys
import os
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.getcwd())

from app.main import app

def test_schedules():
    print("Initializing TestClient...")
    with TestClient(app) as client:
        
        # 1. Test Admin Restriction on GET /api/v1/schedules
        print("\n1. Testing GET /api/v1/schedules (Should fail without auth)...")
        response = client.get("/api/v1/schedules")
        print(f"Response Status: {response.status_code}")
        if response.status_code in [401, 403]:
             print("✅ Access denied as expected.")
        else:
             print(f"❌ Unexpected status code: {response.status_code}")
             print(response.text)

        # 2. Test Public Access to GET /api/v1/schedules/upcoming-schedule
        print("\n2. Testing GET /api/v1/schedules/upcoming-schedule (Should succeed)...")
        response = client.get("/api/v1/schedules/upcoming-schedule")
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
             print("✅ Access granted.")
             print("Response sample:", response.json()[:1] if response.json() else "[]")
        else:
             print(f"❌ Failed to access public endpoint. Status: {response.status_code}")
             print(response.text)

if __name__ == "__main__":
    test_schedules()
