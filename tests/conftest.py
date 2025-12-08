"""Pytest configuration and fixtures for all tests."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import close_mongodb_connection, connect_to_mongodb, get_database
from app.main import create_app


@pytest.fixture
def anyio_backend():
    """Force anyio to use asyncio backend."""
    return "asyncio"


@pytest.fixture
async def setup_db() -> AsyncGenerator[None, None]:
    """Setup and teardown MongoDB for tests."""
    await connect_to_mongodb()
    # Ensure clean slate
    db = get_database()  # type: ignore[assignment]
    await db.client.drop_database(db.name)  # type: ignore[attr-defined]

    yield

    # Cleanup: drop test database
    await db.client.drop_database(db.name)  # type: ignore[attr-defined]
    await close_mongodb_connection()


@pytest.fixture
async def client(
    setup_db: AsyncGenerator[None, None]
) -> AsyncGenerator[AsyncClient, None]:  # noqa: ARG001
    """Provide an async HTTP client for testing."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def pytest_runtest_logreport(report: Any) -> None:  # type: ignore[no-untyped-def]
    """Print test results after each test call phase."""
    # We only care about the actual test call (not setup/teardown)
    if report.when != "call":
        return

    if report.passed:
        status = "PASSED"
        icon = "[PASS]"
    elif report.failed:
        status = "FAILED"
        icon = "[FAIL]"
    else:
        status = "SKIPPED"
        icon = "[SKIP]"

    # Extract test name from nodeid
    # nodeid: tests/api/test_auth.py::test_login_successful
    test_name = report.nodeid.split("::")[-1]
    duration = report.duration

    print(f"\n{icon} {test_name} ... {status} ({duration:.2f}s)")
