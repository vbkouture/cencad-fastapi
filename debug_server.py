
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.getcwd())

from app.main import app

# We need to ensure the DB is connected because the endpoint depends on it.
# The lifespan manager should handle it with TestClient.

def debug_request():
    print("Initializing TestClient...")
    with TestClient(app) as client:
        print("Making request to /api/v1/courses...")
        try:
            response = client.get("/api/v1/courses")
            print(f"Response Status: {response.status_code}")
            if response.status_code != 200:
                print("Response Text:")
                print(response.text)
        except Exception as e:
            print(f"Request failed with exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_request()
