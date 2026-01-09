"""Contact form endpoints: create, list (admin only), and delete (admin only)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.v1.schemas.contact_form_dto import (
    ContactFormRequest,
    ContactFormResponse,
    ContactFormStatusUpdateRequest,
)
from app.core.dependencies import get_current_user_id, require_admin
from app.core.email_service import send_admin_notification_email, send_contact_form_email
from app.db import ContactFormRepository, get_database
from app.domain.users.value_objects import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact-forms", tags=["contact-forms"])


@router.post("", response_model=ContactFormResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    request: ContactFormRequest,
) -> ContactFormResponse:
    """
    Submit a new contact form.

    Anyone can submit a contact form.

    - **name**: Submitter's name
    - **email**: Submitter's email
    - **subject**: Contact form subject
    - **message**: Contact form message

    Returns the created contact form on success.
    """
    db = get_database()
    contact_form_repo = ContactFormRepository(db)

    # Create contact form in MongoDB
    contact_form_doc = await contact_form_repo.create(
        name=request.name,
        email=request.email,
        subject=request.subject,
        message=request.message,
    )

    # Send confirmation email to submitter
    await send_contact_form_email(
        recipient_email=request.email,
        recipient_name=request.name,
        subject=request.subject,
        message=request.message,
    )

    # Send notification email to admin (configured in settings)
    from app.core.config import settings

    if settings.mailtrap_api_token:  # Only send if API token is configured
        # You can configure admin email in settings or use a default
        admin_email = settings.mailtrap_sender_email  # Using sender email as fallback
        await send_admin_notification_email(
            admin_email=admin_email,
            submitter_name=request.name,
            submitter_email=request.email,
            subject=request.subject,
            message=request.message,
        )

    logger.info(f"Contact form submitted by {request.email}: {request.subject}")

    return ContactFormResponse.from_document(contact_form_doc)


@router.get("", response_model=list[ContactFormResponse])
async def list_contact_forms(
    _: UserRole = Depends(require_admin),
) -> list[ContactFormResponse]:
    """
    List all contact form submissions.

    Admin only.

    Returns a list of all contact forms sorted by most recent first.
    """
    db = get_database()
    contact_form_repo = ContactFormRepository(db)

    contact_forms = await contact_form_repo.get_all()
    return [ContactFormResponse.from_document(form) for form in contact_forms]


@router.delete("/{form_id}")
async def delete_contact_form(
    form_id: str,
    _: str = Depends(get_current_user_id),
    __: UserRole = Depends(require_admin),
) -> Response:
    """
    Delete a contact form submission.

    Admin only.

    - **form_id**: The ID of the contact form to delete

    Returns 204 No Content on success.
    """
    db = get_database()
    contact_form_repo = ContactFormRepository(db)

    success = await contact_form_repo.delete(form_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact form not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{form_id}/status", response_model=ContactFormResponse)
async def update_contact_form_status(
    form_id: str,
    request: ContactFormStatusUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    _: UserRole = Depends(require_admin),
) -> ContactFormResponse:
    """
    Update the status of a contact form submission.

    Admin only.

    - **form_id**: The ID of the contact form to update
    - **status**: New status (PENDING, READ, IN_PROGRESS, REPLIED, DISCARDED)
    - **note**: Optional note explaining the change

    Returns the updated contact form.
    """
    db = get_database()
    contact_form_repo = ContactFormRepository(db)

    updated_doc = await contact_form_repo.update_status(
        form_id=form_id,
        status=request.status,
        user_id=current_user_id,
        note=request.note,
    )

    if not updated_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact form not found",
        )

    return ContactFormResponse.from_document(updated_doc)
