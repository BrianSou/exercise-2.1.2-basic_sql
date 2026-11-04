"""Exercise 3.3.1: both complaint writes must succeed or both roll back."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError

from legacy.build_database import seed
from src.api.dependencies import get_complaint_service
from src.api.main import create_app
from src.data.database_manager import DatabaseManager
from src.services.dependencies import build_complaint_service


@pytest.fixture
def api(tmp_path):
    # Every test gets a fresh database. The real training data is untouched.
    path = tmp_path / "transaction_test.db"
    seed(path)
    db = DatabaseManager(path)
    app = create_app()
    app.dependency_overrides[get_complaint_service] = lambda: build_complaint_service(db)
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()
        db.dispose()


def complaint_body():
    return {
        "complaint_id": "CMP999",
        "customer_id": "CUS001",
        "account_id": "ACC001",
        "category": "Fee Dispute",
        "priority": "High",
        "created_by": "EMP001",
        "complaint_text": "Incorrect fee",
    }


def rows_for(db, complaint_id="CMP999"):
    """Read both tables after the API request has finished."""
    with db.session() as session:
        complaint_count = session.scalar(
            text("SELECT COUNT(*) FROM complaint WHERE complaint_id = :id"),
            {"id": complaint_id},
        )
        history = session.execute(
            text("SELECT old_status, new_status FROM complaint_status_history "
                 "WHERE complaint_id = :id ORDER BY history_id"),
            {"id": complaint_id},
        ).all()
        return complaint_count, history


def inject_second_insert_failure(db):
    """Force a database failure only when the opening history INSERT runs."""
    seen = []

    def reject_history(connection, cursor, statement, parameters, context, executemany):
        normalized = statement.strip().lower()
        if normalized.startswith("insert into complaint "):
            seen.append("complaint_insert")
        if normalized.startswith("insert into complaint_status_history"):
            seen.append("history_insert")
            raise OperationalError(statement, parameters, RuntimeError("private database details"))

    event.listen(db.engine, "before_cursor_execute", reject_history)
    return reject_history, seen


def test_success_saves_complaint_and_initial_event(api):
    client, db = api
    response = client.post("/complaints", json=complaint_body())
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "OPEN"
    assert rows_for(db) == (1, [(None, "OPEN")])


def test_second_insert_failure_rolls_back_both_and_returns_safe_error(api):
    client, db = api
    before = rows_for(db)
    reject, seen = inject_second_insert_failure(db)
    try:
        response = client.post("/complaints", json=complaint_body())
    finally:
        event.remove(db.engine, "before_cursor_execute", reject)

    assert seen == ["complaint_insert", "history_insert"]
    assert response.status_code == 503
    assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    assert "private database details" not in response.text
    assert rows_for(db) == before == (0, [])
    assert client.get("/complaints/CMP001").status_code == 200


def test_after_failure_same_id_can_be_created_successfully(api):
    client, db = api
    reject, _ = inject_second_insert_failure(db)
    try:
        assert client.post("/complaints", json=complaint_body()).status_code == 503
    finally:
        event.remove(db.engine, "before_cursor_execute", reject)

    assert client.post("/complaints", json=complaint_body()).status_code == 201
    assert rows_for(db) == (1, [(None, "OPEN")])


def test_invalid_history_actor_rolls_back_both(api):
    client, db = api
    body = complaint_body()
    body["created_by"] = "EMP404"  # Violates history.changed_by foreign key.
    result = client.post("/complaints", json=body)
    assert result.status_code == 409
    assert result.json()["code"] == "CONFLICT"
    assert rows_for(db) == (0, [])


def test_repeating_same_request_does_not_add_duplicate_rows(api):
    client, db = api
    assert client.post("/complaints", json=complaint_body()).status_code == 201
    duplicate = client.post("/complaints", json=complaint_body())
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "CONFLICT"
    assert rows_for(db) == (1, [(None, "OPEN")])


def test_status_update_also_rolls_back_when_history_fails(api):
    client, db = api
    assert client.post("/complaints", json=complaint_body()).status_code == 201
    reject, seen = inject_second_insert_failure(db)
    try:
        response = client.patch("/complaints/CMP999/status", json={
            "status": "IN_PROGRESS", "changed_by": "EMP001"
        })
    finally:
        event.remove(db.engine, "before_cursor_execute", reject)

    assert response.status_code == 503
    assert "history_insert" in seen
    assert client.get("/complaints/CMP999").json()["status"] == "OPEN"
    assert rows_for(db) == (1, [(None, "OPEN")])


def test_invalid_request_leaves_database_unchanged(api):
    client, db = api
    body = complaint_body()
    body["priority"] = "Unrecognized"
    assert client.post("/complaints", json=body).status_code == 422
    assert rows_for(db) == (0, [])


def test_existing_data_is_not_modified_by_failed_create(api):
    client, db = api
    with db.session() as session:
        old_count = session.scalar(text("SELECT COUNT(*) FROM complaint"))
    reject, _ = inject_second_insert_failure(db)
    try:
        assert client.post("/complaints", json=complaint_body()).status_code == 503
    finally:
        event.remove(db.engine, "before_cursor_execute", reject)
    with db.session() as session:
        assert session.scalar(text("SELECT COUNT(*) FROM complaint")) == old_count
    assert rows_for(db) == (0, [])
