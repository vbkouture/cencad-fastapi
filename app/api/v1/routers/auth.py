"""Authentication endpoints: signup and login with MongoDB."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas.auth_dto import LoginRequest, LoginResponse, SignupRequest
from app.core.security import create_access_token, hash_password, verify_password
from app.db import UserRepository, get_database
from app.domain.users.value_objects import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest) -> LoginResponse:
    """
    Create a new user account.

    - **email**: User email (must be unique)
    - **password**: Password (min 8 characters)
    - **name**: User's full name

    New users are created as **student** by default.
    Admins can promote users to tutor/admin roles using admin endpoints.

    Returns a JWT token and user info on success.
    """
    db = get_database()
    user_repo = UserRepository(db)

    hashed_pwd = hash_password(request.password)

    try:
        # Create new user in MongoDB (always as STUDENT)
        user_doc = await user_repo.create_user(
            email=request.email.lower(),
            name=request.name,
            hashed_password=hashed_pwd,
            role=UserRole.STUDENT,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Convert MongoDB ObjectId to string
    user_id = str(user_doc["_id"])

    # Generate JWT token
    token = create_access_token(data={"sub": user_id, "role": UserRole.STUDENT})

    return LoginResponse(
        access_token=token,
        user_id=user_id,
        email=request.email.lower(),
        name=request.name,
        role=UserRole.STUDENT,
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user and receive JWT token.

    - **email**: User email
    - **password**: User password

    Returns a JWT token and user info on successful authentication.
    """
    db = get_database()
    user_repo = UserRepository(db)

    # Find user by email in MongoDB
    user_doc = await user_repo.find_by_email(request.email)

    if user_doc is None or not user_doc.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Convert MongoDB ObjectId to string
    user_id = str(user_doc["_id"])

    # Generate JWT token
    token = create_access_token(data={"sub": user_id, "role": user_doc["role"]})

    return LoginResponse(
        access_token=token,
        user_id=user_id,
        email=user_doc["email"],
        name=user_doc["name"],
        role=UserRole(user_doc["role"]),
    )
