"""FastAPI dependencies for the Week 3 complaint API."""

from fastapi import HTTPException

from src.data.database_manager import DatabaseManager
from src.dependencies import get_engine
from src.services.dependencies import build_complaint_service


def get_complaint_service():
    """Create a service backed by SQLAlchemy repositories.

    The engine is shared, but each repository operation opens its own session.
    Tests can replace this dependency with a service using an isolated database.
    """
    try:
        db = DatabaseManager(engine=get_engine())
        return build_complaint_service(db)
    except Exception:
        # Do not return connection strings or passwords to an API caller.
        raise HTTPException(status_code=503, detail="Database unavailable") from None
