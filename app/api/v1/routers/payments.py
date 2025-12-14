"""Payment router."""

from typing import Annotated, Any

import stripe
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import get_current_user_id
from app.db import get_database
from app.db.course_repository import CourseRepository
from app.db.enrollment_repository import EnrollmentRepository
from app.db.schedule_repository import ScheduleRepository

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/payments", tags=["payments"])


class CheckoutSessionRequest(BaseModel):
    """Request to create a checkout session."""

    schedule_id: str = Field(..., description="ID of the schedule to enroll in")


async def get_schedule_repository() -> ScheduleRepository:
    """Dependency to get schedule repository."""
    return ScheduleRepository(get_database())


async def get_course_repository() -> CourseRepository:
    """Dependency to get course repository."""
    return CourseRepository(get_database())


async def get_enrollment_repository() -> EnrollmentRepository:
    """Dependency to get enrollment repository."""
    return EnrollmentRepository(get_database())


@router.post("/checkout/session", summary="Create Stripe Checkout Session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    schedule_repo: Annotated[ScheduleRepository, Depends(get_schedule_repository)],
    course_repo: Annotated[CourseRepository, Depends(get_course_repository)],
) -> dict[str, str]:
    """
    Create a Stripe Checkout Session for enrolling in a schedule.

    Returns a URL to redirect the user to.
    """
    # 1. Fetch Schedule
    schedule = await schedule_repo.find_by_id(request.schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # 2. Fetch Course (for price)
    course_id = str(schedule["course_id"])
    course = await course_repo.find_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course associated with schedule not found")

    # Check if price exists
    price = course.get("cost")
    if price is None:
        raise HTTPException(status_code=400, detail="Course has no price defined")

    # Convert price to cents (assuming cost is in dollars/float)
    price_cents = int(price * 100)

    try:
        # 3. Create Stripe Session
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            success_url=f"{settings.frontend_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/checkout/cancel",
            client_reference_id=current_user_id,
            line_items=[
                {
                    "price_data": {
                        "currency": "cad",  # Fixed to CAD as requested
                        "product_data": {
                            "name": course["title"],
                            "description": f"Enrollment for {course['title']}",
                            # "images": [course["image"]] if course.get("image") else [],
                        },
                        "unit_amount": price_cents,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "user_id": current_user_id,
                "schedule_id": request.schedule_id,
                "course_id": course_id,
            },
            payment_intent_data={
                "metadata": {
                    "user_id": current_user_id,
                    "schedule_id": request.schedule_id,
                    "course_id": course_id,
                }
            },
        )

        if not checkout_session.url:
            raise HTTPException(status_code=500, detail="Failed to generate checkout URL")

        return {"url": checkout_session.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook", summary="Stripe Webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    enrollment_repo: Annotated[EnrollmentRepository, Depends(get_enrollment_repository)],
) -> dict[str, bool]:
    """
    Handle Stripe webhooks.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)  # type: ignore
    except ValueError:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await _handle_checkout_session_completed(session, enrollment_repo)

    return {"received": True}


async def _handle_checkout_session_completed(
    session: dict[str, Any], repo: EnrollmentRepository
) -> None:
    """
    Process successful checkout session.
    """
    # Verify payment status
    if session.get("payment_status") != "paid":
        return

    # Extract metadata
    metadata = session.get("metadata", {})
    user_id = metadata.get("user_id")
    schedule_id = metadata.get("schedule_id")
    course_id = metadata.get("course_id")

    if not all([user_id, schedule_id, course_id]):
        print(f"Missing metadata in session {session.get('id')}")
        return

    # Idempotency check: Check if enrollment exists with this checkout session ID
    existing = await repo.collection.find_one({"stripe_checkout_session_id": session.get("id")})
    if existing:
        print(f"Enrollment already processed for session {session.get('id')}")
        return

    # Check if student already enrolled via other means (optional overlap check)
    # For now, we assume we just create it or return if exists
    # The repository unique index on (user_id, schedule_id) might raise DuplicateKeyError
    # if we blindly insert. We should check that too.

    existing_enrollment = await repo.collection.find_one(
        {"user_id": ObjectId(user_id), "schedule_id": ObjectId(schedule_id)}
    )

    if existing_enrollment:
        # If they are already enrolled but this is a new payment?
        # Likely a re-payment or error. We might want to update the payment info
        # if the previous one was pending.
        # For simplicity: Update the existing enrollment with new payment details
        pass
        # Logic to update would go here
    else:
        # Create new enrollment
        await repo.create_enrollment(
            user_id=user_id,
            schedule_id=schedule_id,
            course_id=course_id,
            amount_total=session.get("amount_total"),
            currency=session.get("currency", "cad"),
            stripe_checkout_session_id=session.get("id"),
            stripe_payment_intent_id=session.get("payment_intent"),
            stripe_customer_id=session.get("customer"),
            payment_status="PAID",
        )
