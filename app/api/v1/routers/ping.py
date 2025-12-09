from fastapi import APIRouter
from typing_extensions import TypedDict

router = APIRouter(tags=["meta"])


class PingOut(TypedDict):
    ok: bool
    service: str


@router.get("/ping", summary="Liveness ping")
async def ping() -> PingOut:
    """
    A simple read-only endpoint to verify the app is alive.
    Returns a tiny JSON document; safe to call without auth.
    """
    return PingOut(ok=True, service="fastapi-mongo-starter")
