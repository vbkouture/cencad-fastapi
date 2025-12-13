import httpx
import asyncio

async def test_endpoint():
    try:
        async with httpx.AsyncClient() as client:
            print("Sending request to http://127.0.0.1:8000/api/v1/schedules/upcoming-schedule")
            response = await client.get("http://127.0.0.1:8000/api/v1/schedules/upcoming-schedule", timeout=10.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoint())
