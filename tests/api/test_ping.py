import pytest
from httpx import AsyncClient

from app.main import create_app


@pytest.mark.anyio
async def test_ping_returns_ok_and_service_name():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/ping")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert data.get("service") == "fastapi-mongo-starter"
