import json
import urllib.request
import urllib.error
from typing import Any

BASE_URL = "http://127.0.0.1:8000/api/v1"

def make_request(method: str, endpoint: str, data: dict[str, Any] | None = None) -> tuple[int, Any]:
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    req = urllib.request.Request(url, method=method, headers=headers)
    
    if data:
        json_data = json.dumps(data).encode("utf-8")
        req.data = json_data

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")
            try:
                return status_code, json.loads(response_body)
            except json.JSONDecodeError:
                return status_code, response_body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"Failed to connect to {url}: {e}")
        return 0, str(e)

def test_endpoint(name: str, method: str, endpoint: str, data: dict[str, Any] | None = None):
    print(f"Testing {name} ({method} {endpoint})...")
    status_code, response = make_request(method, endpoint, data)
    
    print(f"  Status: {status_code}")
    
    if status_code in [401, 403]:
        print("  ✅ Access Denied (Secure)")
    elif status_code in [404, 422, 200, 201, 204, 500]:
        print(f"  ❌ Access Allowed (Insecure) - Reached handler (Status: {status_code})")
    else:
        print(f"  ❓ Unexpected Status: {status_code}")
    print("-" * 40)

def main():
    print("🔒 Verifying API Access Control (No Auth Token)\n")

    # 1. Schedules (Suspected Insecure)
    # We use a dummy ID. If it returns 404, it means it passed auth and tried to find it.
    # If it returns 401/403, it stopped at auth.
    dummy_id = "507f1f77bcf86cd799439011" 
    
    test_endpoint("Create Schedule", "POST", "/schedules/", {
        "course_id": dummy_id,
        "tutor_id": dummy_id,
        "start_date": "2025-01-01",
        "end_date": "2025-02-01",
        "days": ["Monday"],
        "start_time": "10:00",
        "end_time": "12:00",
        "capacity": 20,
        "timezone": "UTC"
    })
    
    test_endpoint("Update Schedule", "PUT", f"/schedules/{dummy_id}", {
        "capacity": 30
    })
    
    test_endpoint("Delete Schedule", "DELETE", f"/schedules/{dummy_id}")

    # 2. Enrollments (Suspected Insecure)
    test_endpoint("Get Enrollments by Schedule", "GET", f"/enrollments/schedule/{dummy_id}")
    
    test_endpoint("Get Enrollment by ID", "GET", f"/enrollments/{dummy_id}")
    
    test_endpoint("Update Enrollment", "PUT", f"/enrollments/{dummy_id}", {
        "status": "COMPLETED"
    })

    # 3. Courses (Control - Should be Secure)
    test_endpoint("Create Course (Control)", "POST", "/courses", {
        "title": "Hacked Course",
        "description": "Should not work",
        "duration": "1h",
        "level": "BEGINNER",
        "courseDetails": {
            "overview": "test",
            "objectives": [],
            "prerequisites": [],
            "syllabus": []
        }
    })

if __name__ == "__main__":
    main()
