"""Exercise 3.2.2: test the actual HTTP endpoints with an isolated SQLAlchemy database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from legacy.build_database import seed
from src.api.dependencies import get_complaint_service
from src.api.main import create_app
from src.data.database_manager import DatabaseManager
from src.services.dependencies import build_complaint_service


@pytest.fixture
def api(tmp_path):
    database_path = tmp_path / "api_test.db"
    seed(database_path)
    db = DatabaseManager(database_path)
    app = create_app()
    app.dependency_overrides[get_complaint_service] = lambda: build_complaint_service(db)
    with TestClient(app) as client:
        yield client, db
    app.dependency_overrides.clear()
    db.dispose()


def new_complaint(**extra):
    body = {
        "complaint_id": "CMP999",
        "customer_id": "CUS001",
        "category": "Fee Dispute",
        "priority": "High",
        "created_by": "EMP001",
        "account_id": "ACC001",
        "complaint_text": "Fee charged twice",
        "channel": "Web",
    }
    body.update(extra)
    return body


def test_get_customer(api):
    client, _ = api
    response = client.get("/customers/CUS001")
    assert response.status_code == 200
    assert response.json()["customer_id"] == "CUS001"
    assert response.json()["first_name"] == "William"


def test_missing_customer_returns_404(api):
    client, _ = api
    assert client.get("/customers/CUS404").status_code == 404


def test_get_complaint(api):
    client, _ = api
    response = client.get("/complaints/CMP001")
    assert response.status_code == 200
    assert response.json()["status"] == "OPEN"
    assert response.json()["customer_id"] == "CUS001"


def test_missing_complaint_returns_404(api):
    client, _ = api
    assert client.get("/complaints/CMP404").status_code == 404


def test_get_customer_complaints(api):
    client, _ = api
    response = client.get("/customers/CUS001/complaints")
    assert response.status_code == 200
    assert response.json()
    assert all(item["customer_id"] == "CUS001" for item in response.json())


def test_missing_customer_complaints_404(api):
    client, _ = api
    assert client.get("/customers/CUS404/complaints").status_code == 404


def test_existing_customer_no_complaints_returns_empty_list(api):
    client, db = api
    # An existing customer without complaints must return [] (not 404).
    with db.session() as session:
        session.execute(text("INSERT INTO customer (customer_id, first_name, last_name) "
                             "VALUES ('CUS888', 'No', 'Complaints')"))
    response = client.get("/customers/CUS888/complaints")
    assert response.status_code == 200
    assert response.json() == []


def test_post_returns_201_and_open_status(api):
    client, db = api
    response = client.post("/complaints", json=new_complaint())
    assert response.status_code == 201, response.text
    assert response.json()["complaint_id"] == "CMP999"
    assert response.headers["Location"] == "/complaints/CMP999"
    assert response.json()["status"] == "OPEN"
    assert client.get("/complaints/CMP999").status_code == 200
    with db.session() as session:
        history = session.execute(text(
            "SELECT old_status, new_status FROM complaint_status_history "
            "WHERE complaint_id = 'CMP999'"
        )).mappings().all()
    assert [(h["old_status"], h["new_status"]) for h in history] == [(None, "OPEN")]


def test_post_without_account_is_allowed(api):
    client, _ = api
    response = client.post("/complaints", json=new_complaint(account_id=None))
    assert response.status_code == 201, response.text
    assert response.json()["account_id"] is None


def test_post_missing_customer_is_404(api):
    client, _ = api
    response = client.post("/complaints", json=new_complaint(customer_id="CUS404"))
    assert response.status_code == 404


def test_post_wrong_account_is_422(api):
    client, _ = api
    response = client.post("/complaints", json=new_complaint(account_id="ACC002"))
    assert response.status_code == 422


def test_post_duplicate_is_409(api):
    client, _ = api
    assert client.post("/complaints", json=new_complaint()).status_code == 201
    assert client.post("/complaints", json=new_complaint()).status_code == 409


@pytest.mark.parametrize("updates", [
    {"category": "Not a category"},
    {"priority": "Urgent"},
    {"created_by": ""},
    {"customer_id": ""},
    {"complaint_id": ""},
    {"surprise_field": True},
    {"account_id": 45},
])
def test_invalid_post_body_returns_422(api, updates):
    client, _ = api
    assert client.post("/complaints", json=new_complaint(**updates)).status_code == 422


def test_post_missing_required_field_422(api):
    client, _ = api
    body = new_complaint()
    del body["priority"]
    assert client.post("/complaints", json=body).status_code == 422


def test_patch_status_and_history(api):
    client, db = api
    assert client.post("/complaints", json=new_complaint()).status_code == 201
    response = client.patch("/complaints/CMP999/status", json={
        "status": "IN_PROGRESS", "changed_by": "EMP001", "comments": "Working on it"
    })
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "IN_PROGRESS"
    assert client.get("/complaints/CMP999").json()["status"] == "IN_PROGRESS"
    with db.session() as session:
        events = session.execute(text(
            "SELECT old_status, new_status, comments "
            "FROM complaint_status_history WHERE complaint_id='CMP999' "
            "ORDER BY history_id"
        )).mappings().all()
    assert [(e["old_status"], e["new_status"]) for e in events] == [
        (None, "OPEN"), ("OPEN", "IN_PROGRESS")
    ]
    assert events[-1]["comments"] == "Working on it"


def test_invalid_transition_returns_409_and_does_not_write(api):
    client, db = api
    assert client.post("/complaints", json=new_complaint()).status_code == 201
    response = client.patch("/complaints/CMP999/status", json={
        "status": "CLOSED", "changed_by": "EMP001"
    })
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"
    with db.session() as session:
        status = session.execute(text("SELECT status FROM complaint WHERE complaint_id='CMP999'"))
        count = session.execute(text("SELECT count(*) FROM complaint_status_history "
                                     "WHERE complaint_id='CMP999'"))
        assert status.scalar_one() == "OPEN"
        assert count.scalar_one() == 1


def test_escalated_original_schema_is_409(api):
    client, _ = api
    assert client.post("/complaints", json=new_complaint()).status_code == 201
    response = client.patch("/complaints/CMP999/status", json={
        "status": "ESCALATED", "changed_by": "EMP001"
    })
    assert response.status_code == 409


def test_patch_unknown_complaint_404(api):
    client, _ = api
    assert client.patch("/complaints/CMP404/status", json={
        "status": "IN_PROGRESS", "changed_by": "EMP001"
    }).status_code == 404


@pytest.mark.parametrize("body", [
    {"status": "WAITING", "changed_by": "EMP001"},
    {"status": "IN_PROGRESS"},
    {"status": "IN_PROGRESS", "changed_by": ""},
    {"status": "IN_PROGRESS", "changed_by": "EMP001", "ignored": 4},
])
def test_patch_invalid_body_is_422(api, body):
    client, _ = api
    assert client.patch("/complaints/CMP001/status", json=body).status_code == 422


def test_patch_missing_employee_fails_without_partial_update(api):
    client, db = api
    assert client.post("/complaints", json=new_complaint()).status_code == 201
    result = client.patch("/complaints/CMP999/status", json={
        "status": "IN_PROGRESS", "changed_by": "EMP404"
    })
    assert result.status_code == 409
    assert "EMP404" not in result.text
    with db.session() as session:
        assert session.execute(text("SELECT status FROM complaint "
                                    "WHERE complaint_id = 'CMP999' ")).scalar_one() == "OPEN"
        assert session.execute(text("SELECT COUNT(*) FROM complaint_status_history "
                                    "WHERE complaint_id = 'CMP999' ")).scalar_one() == 1


def test_service_dependency_is_replaceable_without_real_postgres(api):
    client, _ = api
    assert client.get("/customers/CUS001").status_code == 200
    assert client.get("/health/live").status_code == 200


def test_documented_openapi_contract(api):
    client, _ = api
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert set([
        "/customers/{id}", "/customers/{id}/complaints",
        "/complaints/{id}", "/complaints",
        "/complaints/{id}/status",
    ]).issubset(paths)
    assert "get" in paths["/customers/{id}"]
    assert "post" in paths["/complaints"]
    assert "patch" in paths["/complaints/{id}/status"]
    assert "201" in paths["/complaints"]["post"]["responses"]
    assert client.get("/docs").status_code == 200
