import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/api/v1/schedules/"

try:
    with urllib.request.urlopen(url) as response:
        print(f"✅ GET {url} - Status: {response.getcode()}")
        data = json.loads(response.read().decode("utf-8"))
        print(f"   Response: {len(data)} schedules")
except urllib.error.HTTPError as e:
    print(f"❌ GET {url} - Status: {e.code}")
    print(f"   Reason: {e.reason}")
except Exception as e:
    print(f"❌ Error: {e}")
