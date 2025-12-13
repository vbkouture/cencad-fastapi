import asyncio
from datetime import datetime
from app.db import get_database, connect_to_mongodb
from app.api.v1.routers.schedules import get_upcoming_schedules
from app.db.schedule_repository import ScheduleRepository

async def inspect():
    await connect_to_mongodb()
    db = get_database()
    repo = ScheduleRepository(db)
    
    print("--- All Schedules ---")
    all_docs = await repo.collection.find().to_list(length=None)
    for doc in all_docs:
        print(f"ID: {doc.get('_id')}")
        print(f"Status: {doc.get('status')}")
        sessions = doc.get('sessions', [])
        print(f"Sessions: {len(sessions)}")
        for s in sessions:
            print(f"  - {s.get('date')} {s.get('start_time')}")
        print("-" * 20)

    print("\n--- Upcoming Query Result ---")
    upcoming = await repo.get_upcoming_schedules()
    print(f"Found {len(upcoming)} upcoming schedules via Repository")

if __name__ == "__main__":
    asyncio.run(inspect())
