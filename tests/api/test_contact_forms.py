"""Tests for contact forms endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_submit_contact_form_success(client: AsyncClient) -> None:
    """Test successful contact form submission."""
    response = await client.post(
        "/api/v1/contact-forms",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a test message",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["subject"] == "Test Subject"
    assert data["message"] == "This is a test message"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_submit_contact_form_missing_fields(client: AsyncClient) -> None:
    """Test contact form submission with missing required fields."""
    response = await client.post(
        "/api/v1/contact-forms",
        json={
            "name": "John Doe",
            "email": "john@example.com",
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_submit_contact_form_invalid_email(client: AsyncClient) -> None:
    """Test contact form submission with invalid email."""
    response = await client.post(
        "/api/v1/contact-forms",
        json={
            "name": "John Doe",
            "email": "invalid-email",
            "subject": "Test",
            "message": "Test message",
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_contact_forms_unauthorized(client: AsyncClient) -> None:
    """Test listing contact forms without authentication."""
    response = await client.get("/api/v1/contact-forms")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_delete_contact_form_unauthorized(client: AsyncClient) -> None:
    """Test deleting contact form without authentication."""
    response = await client.delete("/api/v1/contact-forms/some-id")
    assert response.status_code == 403
