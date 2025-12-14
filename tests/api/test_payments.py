"""Tests for payment endpoints."""

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.security import create_access_token  # Verify import
from app.db import get_database
from app.db.course_repository import CourseRepository
from app.db.schedule_repository import ScheduleRepository
from app.domain.users.value_objects import UserRole


@pytest.fixture
async def payment_setup(
    setup_db: AsyncGenerator[None, None]
) -> AsyncGenerator[tuple[str, str, str], None]:
    """Setup course and schedule for payment tests."""
    db = get_database()
    course_repo = CourseRepository(db)
    schedule_repo = ScheduleRepository(db)

    # Create course with cost
    course_doc = {
        "title": "Paid Course",
        "description": "Desc",
        "duration": "8 weeks",
        "level": "BEGINNER",
        "cost": 100.0,  # $100
        "status": "PUBLISHED",
        "course_details": {"overview": "Overview", "objectives": [], "syllabus": []},
    }
    course_res = await course_repo.collection.insert_one(course_doc)  # type: ignore
    course_id = str(course_res.inserted_id)

    # Create schedule
    schedule_doc = {
        "course_id": course_res.inserted_id,
        "tutor_id": course_res.inserted_id,  # Fake tutor
        "sessions": [],
        "capacity": 10,
        "status": "UPCOMING",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    schedule_res = await schedule_repo.collection.insert_one(schedule_doc)  # type: ignore
    schedule_id = str(schedule_res.inserted_id)

    # User token
    from bson import ObjectId

    user_id = str(ObjectId())
    token = create_access_token(data={"sub": user_id, "role": UserRole.STUDENT})

    yield course_id, schedule_id, token


class TestPayments:
    """Tests for payment endpoints."""

    @pytest.mark.anyio
    @patch("app.api.v1.routers.payments.stripe")
    async def test_create_checkout_session(
        self,
        mock_stripe: MagicMock,
        client: AsyncClient,
        payment_setup: tuple[str, str, str],
    ) -> None:
        """Test creating checkout session."""
        course_id, schedule_id, token = payment_setup

        # Mock stripe response
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        headers = {"Authorization": f"Bearer {token}"}
        payload = {"schedule_id": schedule_id}

        response = await client.post(
            "/api/v1/payments/checkout/session", json=payload, headers=headers
        )

        if response.status_code != status.HTTP_200_OK:
            print(f"FAILED: {response.status_code} {response.text}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["url"] == "https://checkout.stripe.com/test"

        # Verify stripe call
        mock_stripe.checkout.Session.create.assert_called_once()
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["mode"] == "payment"
        assert call_kwargs["line_items"][0]["price_data"]["unit_amount"] == 10000  # 100 * 100 cents
        assert call_kwargs["metadata"]["schedule_id"] == schedule_id

    @pytest.mark.anyio
    @patch("app.api.v1.routers.payments.stripe")
    async def test_webhook_checkout_completed(
        self,
        mock_stripe: MagicMock,
        client: AsyncClient,
        payment_setup: tuple[str, str, str],
    ) -> None:
        """Test webhook processing."""
        course_id, schedule_id, token = payment_setup

        # Mock webhook event construction
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_status": "paid",
                    "amount_total": 10000,
                    "currency": "cad",
                    "payment_intent": "pi_test_123",
                    "customer": "cus_test_123",
                    "metadata": {
                        "user_id": "5f8d0d55b54764421b7156c3",  # Random valid oid
                        "schedule_id": schedule_id,
                        "course_id": course_id,
                    },
                }
            },
        }
        mock_stripe.Webhook.construct_event.return_value = mock_event

        # Prepare headers for signature
        headers = {"stripe-signature": "verified_signature"}

        # Call webhook
        response = await client.post("/api/v1/payments/webhook", json={}, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["received"] is True

        # Verify enrollment created (need to check DB)
        from app.db import get_database

        db = get_database()
        enrollment = await db["enrollments"].find_one({"stripe_checkout_session_id": "cs_test_123"})
        assert enrollment is not None
        assert enrollment["payment_status"] == "PAID"
        assert enrollment["amount_total"] == 10000
