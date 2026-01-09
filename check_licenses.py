"""Check corporate licenses in the database."""

import asyncio

from app.db.mongo import close_mongodb_connection, connect_to_mongodb, get_database


async def check():
    """Check licenses."""
    await connect_to_mongodb()
    db = get_database()
    licenses = await db["corporate_licenses"].find().to_list(10)
    print(f"Found {len(licenses)} licenses in database")

    for lic in licenses:
        print(f'\nLicense ID: {lic["_id"]}')
        print(
            f'  Corp Account ID: {lic.get("corporate_account_id")} (type: {type(lic.get("corporate_account_id")).__name__})'
        )
        print(f'  Course ID: {lic.get("course_id")}')
        print(f'  Schedule ID: {lic.get("schedule_id")}')
        print(f'  Total seats: {lic.get("total_seats")}')
        print(f'  Status: {lic.get("status")}')

    # Check corporate accounts
    accounts = await db["corporate_accounts"].find().to_list(10)
    print(f"\n\nFound {len(accounts)} corporate accounts")
    for acc in accounts:
        print(f'\nAccount ID: {acc["_id"]}')
        print(f'  Company: {acc.get("company_name")}')
        print(f'  Admin IDs: {acc.get("admin_user_ids")}')

    # Get some courses and schedules for testing
    courses = await db["courses"].find().limit(3).to_list(3)
    print(f"\n\nFound {len(courses)} courses (showing first 3)")
    for course in courses:
        print(f'\nCourse ID: {course["_id"]}')
        print(f'  Title: {course.get("title")}')
        print(f'  Cost: ${course.get("cost")}')

    schedules = await db["schedules"].find().limit(3).to_list(3)
    print(f"\n\nFound {len(schedules)} schedules (showing first 3)")
    for sched in schedules:
        print(f'\nSchedule ID: {sched["_id"]}')
        print(f'  Course ID: {sched.get("course_id")}')
        print(f'  Start Date: {sched.get("start_date")}')

    await close_mongodb_connection()


if __name__ == "__main__":
    asyncio.run(check())
