"""Vendors endpoints: CRUD operations with role-based access control."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Depends

from app.api.v1.schemas.vendor_dto import (
    VendorCreateRequest,
    VendorUpdateRequest,
    VendorResponse,
)
from app.core.dependencies import require_admin
from app.db import get_database
from app.db.vendor_repository import VendorRepository
from fastapi.security import HTTPBearer

router = APIRouter(prefix="/vendors", tags=["vendors"])
security = HTTPBearer(auto_error=False)


@router.get("", response_model=list[VendorResponse])
async def get_all_vendors() -> list[VendorResponse]:
    """
    Get all vendors.

    No authentication required - anyone can read vendors.

    Returns:
        List of all vendors.
    """
    db = get_database()
    repo = VendorRepository(db)

    vendors = await repo.get_all_vendors()

    return [
        VendorResponse(
            id=str(vendor["_id"]),
            name=vendor["name"],
            description=vendor["description"],
            logo=vendor.get("logo"),
            created_at=vendor["created_at"],
            updated_at=vendor["updated_at"],
        )
        for vendor in vendors
    ]


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: str) -> VendorResponse:
    """
    Get a specific vendor by ID.

    No authentication required - anyone can read vendors.

    Args:
        vendor_id: MongoDB ObjectId as string

    Returns:
        Vendor details.

    Raises:
        HTTPException: If vendor not found.
    """
    db = get_database()
    repo = VendorRepository(db)

    vendor = await repo.find_by_id(vendor_id)

    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    return VendorResponse(
        id=str(vendor["_id"]),
        name=vendor["name"],
        description=vendor["description"],
        logo=vendor.get("logo"),
        created_at=vendor["created_at"],
        updated_at=vendor["updated_at"],
    )


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_vendor(
    request: VendorCreateRequest,
    _: str = Depends(require_admin),
) -> VendorResponse:
    """
    Create a new vendor.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        request: Vendor creation request with name, description, and optional logo
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Created vendor.

    Raises:
        HTTPException: If name already exists or validation fails.
    """
    db = get_database()
    repo = VendorRepository(db)

    try:
        vendor = await repo.create_vendor(
            name=request.name,
            description=request.description,
            logo=request.logo,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return VendorResponse(
        id=str(vendor["_id"]),
        name=vendor["name"],
        description=vendor["description"],
        logo=vendor.get("logo"),
        created_at=vendor["created_at"],
        updated_at=vendor["updated_at"],
    )


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    request: VendorUpdateRequest,
    _: str = Depends(require_admin),
) -> VendorResponse:
    """
    Update a vendor.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        vendor_id: MongoDB ObjectId as string
        request: Update request with optional name, description, and/or logo
        _: Admin role requirement (validates JWT token and role)

    Returns:
        Updated vendor.

    Raises:
        HTTPException: If vendor not found, validation fails, or name already exists.
    """
    db = get_database()
    repo = VendorRepository(db)

    try:
        updated_vendor = await repo.update_vendor(
            vendor_id=vendor_id,
            name=request.name,
            description=request.description,
            logo=request.logo,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if updated_vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    return VendorResponse(
        id=str(updated_vendor["_id"]),
        name=updated_vendor["name"],
        description=updated_vendor["description"],
        logo=updated_vendor.get("logo"),
        created_at=updated_vendor["created_at"],
        updated_at=updated_vendor["updated_at"],
    )


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    _: str = Depends(require_admin),
) -> None:
    """
    Delete a vendor.

    **Admin only** - requires valid JWT token with admin role.

    Args:
        vendor_id: MongoDB ObjectId as string
        _: Admin role requirement (validates JWT token and role)

    Raises:
        HTTPException: If vendor not found.
    """
    db = get_database()
    repo = VendorRepository(db)

    deleted = await repo.delete_vendor(vendor_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
