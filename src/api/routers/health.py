"""Health endpoints."""

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas import HealthResponse
from src.dependencies import get_readiness_checker

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
def live():
    """The API process is running."""
    return {"status": "ok"}


@router.get("/ready", response_model=HealthResponse)
def ready(check: Callable[[], bool] = Depends(get_readiness_checker)):
    """The API can reach its PostgreSQL database."""
    try:
        available = check()
    except Exception:
        available = False
    if not available:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ready"}
