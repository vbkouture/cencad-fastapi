"""Certifications endpoints: CRUD operations with role-based access control."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.api.v1.schemas.certification_dto import (
    CertificationCreateRequest,
    CertificationResponse,
    CertificationUpdateRequest,
)
from app.core.dependencies import require_admin
from app.db import get_database
from app.db.certification_repository import CertificationRepository

router = APIRouter(prefix="/certifications", tags=["certifications"])
security = HTTPBearer(auto_error=False)


@router.get("", response_model=list[CertificationResponse])
async def get_all_certifications() -> list[CertificationResponse]:
    """
    Get all certifications.
    """
    db = get_database()
    repo = CertificationRepository(db)

    certs = await repo.get_all_certifications()

    return [
        CertificationResponse(
            id=str(cert["_id"]),
            vendor_id=str(cert["vendor_id"]),
            name=cert["name"],
            description=cert.get("description"),
            url=cert.get("url"),
            created_at=cert["created_at"],
            updated_at=cert["updated_at"],
        )
        for cert in certs
    ]


@router.get("/{cert_id}", response_model=CertificationResponse)
async def get_certification(cert_id: str) -> CertificationResponse:
    """
    Get a specific certification by ID.
    """
    db = get_database()
    repo = CertificationRepository(db)

    cert = await repo.find_by_id(cert_id)

    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found",
        )

    return CertificationResponse(
        id=str(cert["_id"]),
        vendor_id=str(cert["vendor_id"]),
        name=cert["name"],
        description=cert.get("description"),
        url=cert.get("url"),
        created_at=cert["created_at"],
        updated_at=cert["updated_at"],
    )


@router.post(
    "",
    response_model=CertificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_certification(
    request: CertificationCreateRequest,
    _: str = Depends(require_admin),
) -> CertificationResponse:
    """
    Create a new certification.

    **Admin only**
    """
    db = get_database()
    repo = CertificationRepository(db)

    try:
        cert = await repo.create_certification(
            vendor_id=request.vendor_id,
            name=request.name,
            description=request.description,
            url=request.url,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return CertificationResponse(
        id=str(cert["_id"]),
        vendor_id=str(cert["vendor_id"]),
        name=cert["name"],
        description=cert.get("description"),
        url=cert.get("url"),
        created_at=cert["created_at"],
        updated_at=cert["updated_at"],
    )


@router.put("/{cert_id}", response_model=CertificationResponse)
async def update_certification(
    cert_id: str,
    request: CertificationUpdateRequest,
    _: str = Depends(require_admin),
) -> CertificationResponse:
    """
    Update a certification.

    **Admin only**
    """
    db = get_database()
    repo = CertificationRepository(db)

    try:
        updated_cert = await repo.update_certification(
            cert_id=cert_id,
            vendor_id=request.vendor_id,
            name=request.name,
            description=request.description,
            url=request.url,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if updated_cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found",
        )

    return CertificationResponse(
        id=str(updated_cert["_id"]),
        vendor_id=str(updated_cert["vendor_id"]),
        name=updated_cert["name"],
        description=updated_cert.get("description"),
        url=updated_cert.get("url"),
        created_at=updated_cert["created_at"],
        updated_at=updated_cert["updated_at"],
    )


@router.delete("/{cert_id}")
async def delete_certification(
    cert_id: str,
    _: str = Depends(require_admin),
) -> None:
    """
    Delete a certification.

    **Admin only**
    """
    db = get_database()
    repo = CertificationRepository(db)

    deleted = await repo.delete_certification(cert_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found",
        )
