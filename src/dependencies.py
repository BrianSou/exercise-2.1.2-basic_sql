"""SQLAlchemy dependencies used by FastAPI.

No connection is attempted when the module is imported. This lets the API
start even when PostgreSQL is down, so liveness can still respond.
"""

from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.config import Settings


@lru_cache(maxsize=1)
def get_engine():
    settings = Settings.from_environment()
    return create_engine(
        settings.database_url(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


def get_db_session():
    """Database Session for future API routes (Exercise 3.2.2)."""
    with Session(get_engine()) as session:
        yield session


def check_database(engine=None):
    """Health check runs SELECT 1; never return connection details."""
    try:
        active_engine = engine if engine is not None else get_engine()
        with active_engine.connect() as connection:
            return connection.scalar(text("SELECT 1")) == 1
    except Exception:
        return False


def get_readiness_checker():
    """The API can override this callable in tests."""
    return check_database
