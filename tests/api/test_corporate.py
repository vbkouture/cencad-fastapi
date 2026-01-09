import pytest
from bson import ObjectId
from httpx import AsyncClient

from app.db import get_database
from app.domain.corporate.models import CompanySize

# --- Fixtures ---


@pytest.fixture
async def corporate_admin_token(client: AsyncClient) -> tuple[str, str]:
    """
    Register a corporate account and return (access_token, account_id).
    This simulates a full integration flow to set up the test state.
    """
    # Register
    register_data = {
        "company_name": "Test Corp",
        "company_size": CompanySize.SIZE_11_50,
        "admin_name": "Corp Admin",
        "admin_email": "admin@testcorp.com",
        "admin_password": "securepass123",
        "industry": "Tech",
    }
    response = await client.post("/api/v1/corporate/register", json=register_data)
    assert response.status_code == 201
    account_data = response.json()
    account_id = account_data["id"]

    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@testcorp.com",
            "password": "securepass123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return token, account_id


# --- Tests ---


@pytest.mark.anyio
async def test_register_corporate_account_success(client: AsyncClient) -> None:
    """Test successful registration of a corporate account."""
    payload = {
        "company_name": "Acme Inc",
        "company_size": "51-200",
        "admin_name": "Acme Admin",
        "admin_email": "acme@example.com",
        "admin_password": "securepass123",
        "company_website": "https://acme.com",
        "industry": "Manufacturing",
    }
    response = await client.post("/api/v1/corporate/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "Acme Inc"
    assert data["status"] == "ACTIVE"  # Assuming default is active as per model
    assert "id" in data


@pytest.mark.anyio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test registration fails if admin email is already taken."""
    payload = {
        "company_name": "Corp 1",
        "company_size": "1-10",
        "admin_name": "Admin 1",
        "admin_email": "duplicate@corp.com",
        "admin_password": "pass",
    }
    await client.post("/api/v1/corporate/register", json=payload)

    # Try registering again with same email
    payload["company_name"] = "Corp 2"
    response = await client.post("/api/v1/corporate/register", json=payload)
    assert response.status_code == 409
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_my_corporate_account(client: AsyncClient, corporate_admin_token) -> None:
    """Test fetching own corporate account details."""
    token, account_id = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/corporate/account", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == account_id
    assert data["company_name"] == "Test Corp"


@pytest.mark.anyio
async def test_update_corporate_account(client: AsyncClient, corporate_admin_token) -> None:
    """Test updating corporate account details."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {"company_name": "Updated Corp Name", "phone": "+1234567890"}
    response = await client.patch("/api/v1/corporate/account", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Updated Corp Name"
    assert data["phone"] == "+1234567890"


@pytest.mark.anyio
async def test_get_dashboard_stats(client: AsyncClient, corporate_admin_token) -> None:
    """Test fetching dashboard stats."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/corporate/dashboard/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Initial state should be zero/empty
    assert data["total_licenses"] == 0
    assert data["active_trainees"] == 0


@pytest.mark.anyio
async def test_create_checkout_session(client: AsyncClient, corporate_admin_token) -> None:
    """Test creating a mock checkout session."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"course_id": "course_123", "schedule_id": "sched_123", "quantity": 5}
    response = await client.post(
        "/api/v1/corporate/checkout/session", json=payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "session_id" in data


@pytest.mark.anyio
async def test_invite_trainee_new_user(client: AsyncClient, corporate_admin_token) -> None:
    """Test inviting a brand new user as a trainee."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"email": "new.trainee@example.com", "name": "New Trainee"}
    response = await client.post("/api/v1/corporate/trainees/invite", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new.trainee@example.com"
    assert data["is_active"] is True
    # Verify shadow user was created? The endpoint does this internally.
    # We can check by trying to login or checking DB via side-channel if we really wanted to be pure,
    # but the API response confirming the email is good enough for IT.


@pytest.mark.anyio
async def test_invite_trainee_existing_user(client: AsyncClient, corporate_admin_token) -> None:
    """Test inviting a user that already exists in the system."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    # Create a user independently first
    reg_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "existing.user@example.com",
            "password": "password123",
            "name": "Existing User",
        },
    )
    assert reg_response.status_code == 201

    # Now invite them
    payload = {"email": "existing.user@example.com", "name": "Existing User"}
    response = await client.post("/api/v1/corporate/trainees/invite", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "existing.user@example.com"


@pytest.mark.anyio
async def test_invite_duplicate_trainee(client: AsyncClient, corporate_admin_token) -> None:
    """Test inviting the same trainee twice fails."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"email": "trainee.dup@example.com", "name": "Trainee Dup"}
    # First invite
    await client.post("/api/v1/corporate/trainees/invite", json=payload, headers=headers)

    # Second invite
    response = await client.post("/api/v1/corporate/trainees/invite", json=payload, headers=headers)
    assert response.status_code == 409
    assert "already a trainee" in response.json()["detail"]


@pytest.mark.anyio
async def test_list_trainees(client: AsyncClient, corporate_admin_token) -> None:
    """Test listing trainees."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    # Invite 2 trainees
    for i in range(2):
        await client.post(
            "/api/v1/corporate/trainees/invite",
            json={"email": f"trainee{i}@test.com", "name": f"Trainee {i}"},
            headers=headers,
        )

    response = await client.get("/api/v1/corporate/trainees", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.anyio
async def test_remove_trainee(client: AsyncClient, corporate_admin_token) -> None:
    """Test removing a trainee."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}

    # Invite
    invite_res = await client.post(
        "/api/v1/corporate/trainees/invite",
        json={"email": "remove.me@test.com", "name": "Remove Me"},
        headers=headers,
    )
    trainee_id = invite_res.json()["id"]

    # Remove
    del_res = await client.delete(f"/api/v1/corporate/trainees/{trainee_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify removed
    list_res = await client.get("/api/v1/corporate/trainees", headers=headers)
    items = list_res.json()["items"]
    assert not any(t["id"] == trainee_id for t in items)


# --- Assignments Integration ---
# Since we need a License to assign, and we don't have a real payment flow in tests (mocked),
# we need to inject a License directly into the DB or have a "backdoor" if endpoints strictly forbid it.
# However, the checkout mock returns a session URL but doesn't actually create the license callback
# (which would handle the webhook).
# So for IT tests of assignment, we might need a helper to seed a license directly to the DB,
# OR we implement a mock webhook endpoint if possible.
# Simpler approach: Use a fixture to inject a license directly into the DB for the test account.


@pytest.fixture
async def seed_license(corporate_admin_token):
    token, account_id = corporate_admin_token
    db = get_database()

    # Create a license manually in DB
    from app.domain.corporate.models import CorporateLicense, LicenseStatus

    license_id = str(ObjectId())
    schedule_id = str(ObjectId())
    course_id = str(ObjectId())

    lic = CorporateLicense(
        id=license_id,
        corporate_account_id=account_id,
        schedule_id=schedule_id,
        course_id=course_id,
        total_seats=2,
        assigned_seats=0,
        amount_total=100.0,
        currency="usd",
        status=LicenseStatus.ACTIVE,
    )

    # Mimic repository storage format
    doc = lic.model_dump(mode="json")
    doc["_id"] = ObjectId(license_id)
    del doc["id"]

    # Also need to ensure datetime fields are correct if model_dump(mode='json') makes them strings.
    # But wait, create_license uses mode='json'. Let's check if repo handles string dates?
    # Pydantic mode='json' converts datetime to ISO string.
    # MongoDB usually wants datetime objects for queryability, but if the app uses strings consistently it's fine.
    # However, CorporateLicense fields are `datetime`.
    # Let's check if the Repository's create_license does anything else.
    # It just does model_dump(mode="json").
    # So the DB has strings?
    # Let's check Models.
    # created_at: datetime.
    # If using mode='json', they become strings.
    # If the app expects them to be strings in DB (which is rare for Mongo but possible with Pydantic v2), ok.
    # But wait, earlier I saw `created_at=created_account["created_at"]` in response.
    # If it's a string in DB, Pydantic will parse it back to datetime on read if the model says datetime.
    # So mode='json' is fine for insertion if we are consistent.

    # Only fix required is _id mapping.

    await db["corporate_licenses"].insert_one(doc)
    return license_id


@pytest.mark.anyio
async def test_assign_trainee_success(
    client: AsyncClient, corporate_admin_token, seed_license
) -> None:
    """Test assigning a trainee to a valid license."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}
    license_id = seed_license

    # Invite trainee
    invite_res = await client.post(
        "/api/v1/corporate/trainees/invite",
        json={"email": "assign.me@test.com", "name": "Assign Me"},
        headers=headers,
    )
    trainee_id = invite_res.json()["id"]

    # Assign
    assign_res = await client.post(
        "/api/v1/corporate/trainees/assign",
        json={"license_id": license_id, "trainee_id": trainee_id},
        headers=headers,
    )
    assert assign_res.status_code == 200

    # Verify seat count increased
    lic_res = await client.get("/api/v1/corporate/licenses", headers=headers)
    data = lic_res.json()
    my_lic = next(license_item for license_item in data["items"] if license_item["id"] == license_id)
    assert my_lic["assigned_seats"] == 1


@pytest.mark.anyio
async def test_assign_trainee_no_seats(
    client: AsyncClient, corporate_admin_token, seed_license
) -> None:
    """Test assignment fails when no seats are available."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}
    license_id = seed_license

    # Fill up the 2 seats
    for i in range(2):
        u_res = await client.post(
            "/api/v1/corporate/trainees/invite",
            json={"email": f"seat{i}@test.com", "name": f"Seat {i}"},
            headers=headers,
        )
        t_id = u_res.json()["id"]
        await client.post(
            "/api/v1/corporate/trainees/assign",
            json={"license_id": license_id, "trainee_id": t_id},
            headers=headers,
        )

    # Try 3rd assignment
    u_res = await client.post(
        "/api/v1/corporate/trainees/invite",
        json={"email": "seat3@test.com", "name": "Seat 3"},
        headers=headers,
    )
    t_id_3 = u_res.json()["id"]

    response = await client.post(
        "/api/v1/corporate/trainees/assign",
        json={"license_id": license_id, "trainee_id": t_id_3},
        headers=headers,
    )

    assert response.status_code == 400
    assert "No seats available" in response.json()["detail"]


@pytest.mark.anyio
async def test_unassign_trainee(client: AsyncClient, corporate_admin_token, seed_license) -> None:
    """Test unassigning a trainee."""
    token, _ = corporate_admin_token
    headers = {"Authorization": f"Bearer {token}"}
    license_id = seed_license

    # Invite & Assign
    invite_res = await client.post(
        "/api/v1/corporate/trainees/invite",
        json={"email": "unassign@test.com", "name": "Unassign Me"},
        headers=headers,
    )
    trainee_id = invite_res.json()["id"]

    await client.post(
        "/api/v1/corporate/trainees/assign",
        json={"license_id": license_id, "trainee_id": trainee_id},
        headers=headers,
    )

    # Unassign
    unassign_res = await client.post(
        "/api/v1/corporate/trainees/unassign",
        json={"license_id": license_id, "trainee_id": trainee_id},
        headers=headers,
    )
    assert unassign_res.status_code == 200

    # Verify seat count back to 0
    lic_res = await client.get("/api/v1/corporate/licenses", headers=headers)
    my_lic = next(license_item for license_item in lic_res.json()["items"] if license_item["id"] == license_id)
    assert my_lic["assigned_seats"] == 0
