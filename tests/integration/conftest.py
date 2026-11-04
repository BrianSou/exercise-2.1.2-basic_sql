"""Every integration test uses a temporary SQLAlchemy database."""

import os

import pytest
from fastapi.testclient import TestClient

from legacy.build_database import seed
from src.api.dependencies import get_complaint_service
from src.api.main import create_app
from src.data.database_manager import DatabaseManager
from src.services.dependencies import build_complaint_service


def pytest_collection_modifyitems(items):
    # Second assessment run can reverse the order to check test independence.
    if os.environ.get("REVERSE_TEST_ORDER") == "1":
        items.reverse()


@pytest.fixture
def api(tmp_path):
    path = tmp_path / "isolated.db"
    seed(path)
    db = DatabaseManager(path)
    app = create_app()
    app.dependency_overrides[get_complaint_service] = lambda: build_complaint_service(db)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, db, app
    finally:
        app.dependency_overrides.clear()
        db.dispose()
