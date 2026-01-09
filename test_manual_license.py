"""Test creating a corporate license manually."""

import asyncio

import httpx


async def test_manual_license():
    """Test the manual license creation endpoint."""

    # First, login as corporate admin
    login_data = {"email": "admin@acmecorp.com", "password": "SecurePass123!"}

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Login
        print("Logging in...")
        response = await client.post("/api/v1/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} - {response.text}")
            return

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully")

        # Check existing licenses
        print("\nChecking existing licenses...")
        response = await client.get("/api/v1/corporate/licenses?skip=0&limit=20", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['total']} existing licenses")
            for item in data["items"]:
                print(f"  - License {item['id']}: {item['total_seats']} seats")
        else:
            print(f"Failed to get licenses: {response.status_code} - {response.text}")

        # Create a new license manually
        print("\nCreating a new license...")
        license_data = {
            "course_id": "5f8d0d55b54764421b715701",  # Complete Python Bootcamp
            "schedule_id": "5f8d0d55b54764421b715801",  # Schedule starting 2025-01-15
            "quantity": 10,
        }

        response = await client.post(
            "/api/v1/corporate/licenses/create", json=license_data, headers=headers
        )
        if response.status_code == 200:
            license = response.json()
            print("✅ License created successfully!")
            print(f"  ID: {license['id']}")
            print(f"  Course: {license['course_id']}")
            print(f"  Total seats: {license['total_seats']}")
            print(f"  Amount: ${license['amount_total']}")
        else:
            print(f"❌ Failed to create license: {response.status_code}")
            print(f"Response: {response.text}")

        # Check licenses again
        print("\nChecking licenses after creation...")
        response = await client.get("/api/v1/corporate/licenses?skip=0&limit=20", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['total']} licenses now")
            for item in data["items"]:
                print(
                    f"  - License {item['id']}: {item['total_seats']} seats for course {item['course_id']}"
                )


if __name__ == "__main__":
    asyncio.run(test_manual_license())
