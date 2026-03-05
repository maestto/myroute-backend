"""Health endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    """Return backend health status."""
    return {"status": "ok"}

