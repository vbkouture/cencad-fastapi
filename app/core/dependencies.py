"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.domain.users.value_objects import UserRole

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract and validate the user ID from the JWT token in Authorization header.

    Raises:
        HTTPException: If token is invalid or missing required claims.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserRole:
    """
    Extract and validate the user role from the JWT token.

    Raises:
        HTTPException: If token is invalid or missing role.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_str: str | None = payload.get("role")
    if role_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user role",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return UserRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user role in token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(role: UserRole = Depends(get_current_user_role)) -> UserRole:
    """
    Dependency to require admin role.

    Raises:
        HTTPException: If user is not an admin.
    """
    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return role


async def require_tutor(role: UserRole = Depends(get_current_user_role)) -> UserRole:
    """
    Dependency to require tutor role.

    Raises:
        HTTPException: If user is not a tutor or admin.
    """
    if role not in (UserRole.TUTOR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tutor or admin access required",
        )
    return role


async def require_student(role: UserRole = Depends(get_current_user_role)) -> UserRole:
    """
    Dependency to require student role or higher.

    Raises:
        HTTPException: If user role is insufficient.
    """
    if role not in (UserRole.STUDENT, UserRole.TUTOR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return role
