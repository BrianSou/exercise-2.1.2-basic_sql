"""3.4.2: verify HTTP responses and the real persisted database state."""

import json
import logging
from uuid import UUID

from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError

from src.api.dependencies import get_complaint_service
from src.api.logging_config import LOGGER
from src.dependencies import get_readiness_checker


def complaint_body(**changes):
    body = {
        "complaint_id": "CMP999", "customer_id": "CUS001", "account_id": "ACC001",
        "category": "Fee Dispute", "priority": "High", "created_by": "EMP001",
        "complaint_text": "Sensitive complaint narrative: do not log this",
    }
    body.update(changes)
    return body


def state(db):
    with db.session() as session:
        count = session.scalar(text("SELECT COUNT(*) FROM complaint WHERE complaint_id='CMP999'"))
        events = session.execute(text(
            "SELECT old_status, new_status FROM complaint_status_history "
            "WHERE complaint_id='CMP999' ORDER BY history_id"
        )).all()
        return count, events


def assert_error(response, code, status):
    assert response.status_code == status
    payload = response.json()
    assert set(payload) == {"code", "message", "correlation_id"}
    assert payload["code"] == code
    assert payload["correlation_id"] == response.headers["X-Correlation-ID"]
    UUID(payload["correlation_id"])  # Without caller ID, middleware generates a UUID.
    assert "traceback" not in response.text.lower()


def test_customer_get_success_and_missing(api):
    client, _, _ = api
    assert client.get("/customers/CUS001").json()["customer_id"] == "CUS001"
    assert_error(client.get("/customers/CUS404"), "CUSTOMER_NOT_FOUND", 404)


def test_complaint_create_saves_row_and_event(api):
    client, db, _ = api
    response = client.post("/complaints", json=complaint_body())
    assert response.status_code == 201
    assert response.headers["Location"] == "/complaints/CMP999"
    assert state(db) == (1, [(None, "OPEN")])
    assert client.get("/complaints/CMP999").json()["status"] == "OPEN"


def test_missing_complaint_has_stable_error(api):
    client, _, _ = api
    assert_error(client.get("/complaints/CMP404"), "COMPLAINT_NOT_FOUND", 404)


def test_invalid_post_returns_422_without_write(api):
    client, db, _ = api
    response = client.post("/complaints", json=complaint_body(priority="Not Valid"))
    assert_error(response, "VALIDATION_ERROR", 422)
    assert state(db) == (0, [])


def test_status_change_persists_both_status_and_history(api):
    client, db, _ = api
    assert client.post("/complaints", json=complaint_body()).status_code == 201
    changed = client.patch("/complaints/CMP999/status", json={
        "status": "IN_PROGRESS", "changed_by": "EMP001"
    })
    assert changed.status_code == 200
    with db.session() as session:
        stored_status = session.scalar(text("SELECT status FROM complaint WHERE complaint_id='CMP999'"))
    assert stored_status == "IN_PROGRESS"
    assert state(db) == (1, [(None, "OPEN"), ("OPEN", "IN_PROGRESS")])


def test_invalid_transition_is_409_and_does_not_write(api):
    client, db, _ = api
    assert client.post("/complaints", json=complaint_body()).status_code == 201
    response = client.patch("/complaints/CMP999/status", json={
        "status": "CLOSED", "changed_by": "EMP001"
    })
    assert_error(response, "INVALID_STATUS_TRANSITION", 409)
    assert state(db) == (1, [(None, "OPEN")])


def test_history_insert_failure_rolls_back_complaint(api):
    client, db, _ = api

    def reject_history(conn, cursor, statement, parameters, context, many):
        if statement.strip().lower().startswith("insert into complaint_status_history"):
            raise OperationalError(statement, parameters, RuntimeError("do not expose secret database data"))

    event.listen(db.engine, "before_cursor_execute", reject_history)
    try:
        response = client.post("/complaints", json=complaint_body())
    finally:
        event.remove(db.engine, "before_cursor_execute", reject_history)
    assert_error(response, "DEPENDENCY_UNAVAILABLE", 503)
    assert "do not expose secret" not in response.text
    assert state(db) == (0, [])


def test_unavailable_dependency_returns_503(api):
    client, _, app = api
    app.dependency_overrides[get_readiness_checker] = lambda: (lambda: False)
    try:
        assert_error(client.get("/health/ready"), "DEPENDENCY_UNAVAILABLE", 503)
    finally:
        del app.dependency_overrides[get_readiness_checker]


def test_unknown_error_returns_500_without_secrets(api):
    client, _, app = api

    class BrokenService:
        def get_complaint(self, complaint_id):
            raise RuntimeError("secret password and private complaint narrative")

    app.dependency_overrides[get_complaint_service] = lambda: BrokenService()
    response = client.get("/complaints/CMP001")
    assert_error(response, "INTERNAL_ERROR", 500)
    assert "secret password" not in response.text


def test_correlation_id_propagates_without_logging_payload(api):
    client, _, _ = api
    entries = []

    class Capture(logging.Handler):
        def emit(self, record):
            entries.append(json.loads(record.getMessage()))

    capture = Capture()
    LOGGER.addHandler(capture)
    try:
        response = client.post("/complaints", json=complaint_body(),
                               headers={"X-Correlation-ID": "test-correlation-123"})
    finally:
        LOGGER.removeHandler(capture)
    assert response.status_code == 201
    assert response.headers["X-Correlation-ID"] == "test-correlation-123"
    assert entries and entries[-1]["correlation_id"] == "test-correlation-123"
    assert entries[-1]["operation"] == "POST /complaints"
    assert entries[-1]["outcome"] == "success"
    assert entries[-1]["duration_ms"] >= 0
    assert set(entries[-1]) >= {"timestamp", "level", "correlation_id", "operation", "outcome", "duration_ms"}
    assert "Sensitive complaint narrative" not in json.dumps(entries)
    assert "DB_PASSWORD" not in json.dumps(entries)


def test_invalid_correlation_header_is_replaced(api):
    client, _, _ = api
    response = client.get("/health/live", headers={"X-Correlation-ID": "bad id with spaces"})
    assert response.status_code == 200
    UUID(response.headers["X-Correlation-ID"])


def test_documentation_and_health_are_available(api):
    client, _, _ = api
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200
