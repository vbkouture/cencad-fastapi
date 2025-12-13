from datetime import datetime
from pydantic import BaseModel, Field

# --- DTOs (from default api/v1/schemas/schedule_dto.py) ---
class SessionDTO(BaseModel):
    date: datetime = Field(description="Session date")
    start_time: str = Field(description="Start time (e.g., '18:00')")
    end_time: str = Field(description="End time (e.g., '20:00')")

class PublicScheduleResponse(BaseModel):
    id: str = Field(description="Schedule ID")
    course_id: str = Field(description="Course ID")
    sessions: list[SessionDTO] = Field(description="List of sessions")
    capacity: int = Field(description="Maximum capacity")
    timezone: str = Field(description="Timezone")

# --- Domain (from app/domain/schedules/schedule.py) ---
class Session(BaseModel):
    date: datetime
    start_time: str
    end_time: str

class Schedule(BaseModel):
    id: str = Field(alias="_id")
    course_id: str
    sessions: list[Session]
    capacity: int
    timezone: str = "UTC"
    
    class Config:
        populate_by_name = True

# --- Test Logic ---
def test_conversion():
    print("Creating Domain Object...")
    session_domain = Session(
        date=datetime.now(),
        start_time="10:00",
        end_time="12:00"
    )
    schedule_domain = Schedule(
        _id="test_id_123",
        course_id="course_123",
        sessions=[session_domain],
        capacity=20,
        timezone="UTC"
    )
    print(f"Domain Object: {schedule_domain}")

    print("\nAttempting Conversion...")
    try:
        # Simulate the fix I applied
        sessions_dto = [SessionDTO.model_validate(s.model_dump()) for s in schedule_domain.sessions]
        
        response = PublicScheduleResponse(
            id=schedule_domain.id,
            course_id=schedule_domain.course_id,
            sessions=sessions_dto,
            capacity=schedule_domain.capacity,
            timezone=schedule_domain.timezone,
        )
        print("Conversion SUCCESS!")
        print(response)
    except Exception as e:
        print("Conversion FAILED!")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversion()
