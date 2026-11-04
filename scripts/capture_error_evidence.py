"""Reproduce sanitized error and log evidence using a temporary database."""

import csv
import json
import logging
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from legacy.build_database import seed
from src.api.dependencies import get_complaint_service
from src.api.logging_config import LOGGER
from src.api.main import create_app
from src.data.database_manager import DatabaseManager
from src.dependencies import get_readiness_checker
from src.services.dependencies import build_complaint_service

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "exercise_3_3_2"


class Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.items = []

    def emit(self, record):
        self.items.append(json.loads(record.getMessage()))


def make_body():
    return {"complaint_id": "CMP999", "customer_id": "CUS001", "account_id": "ACC001",
            "category": "Fee Dispute", "priority": "High", "created_by": "EMP001",
            "complaint_text": "DO_NOT_LOG_MY_SENSITIVE_NARRATIVE"}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    captured = Capture()
    LOGGER.addHandler(captured)
    rows = []
    try:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.db"
            seed(path)
            db = DatabaseManager(path)
            app = create_app()
            app.dependency_overrides[get_complaint_service] = lambda: build_complaint_service(db)
            try:
                with TestClient(app, raise_server_exceptions=False) as client:
                    def record(name, method, route, expected_status, expected_code, **kwargs):
                        cid = f"evidence-{len(rows)+1:02d}"
                        headers = dict(kwargs.pop("headers", {}))
                        headers["X-Correlation-ID"] = cid
                        response = client.request(method, route, headers=headers, **kwargs)
                        assert response.status_code == expected_status, (name, response.text)
                        content = response.json()
                        assert content["code"] == expected_code
                        assert content["correlation_id"] == cid
                        entry = next(item for item in reversed(captured.items) if item["correlation_id"] == cid)
                        assert entry["status_code"] == response.status_code
                        rows.append({
                            "scenario": name,
                            "http_method": method,
                            "path_template": entry["operation"].split(" ", 1)[1],
                            "status_code": response.status_code,
                            "error_code": content["code"],
                            "message": content["message"],
                            "correlation_id": cid,
                            "logged_operation": entry["operation"],
                            "logged_outcome": entry["outcome"],
                            "safe_response": "yes" if "Traceback" not in response.text else "no",
                        })

                    record("missing_customer", "GET", "/customers/CUS404", 404, "CUSTOMER_NOT_FOUND")
                    record("missing_complaint", "GET", "/complaints/CMP404", 404, "COMPLAINT_NOT_FOUND")
                    record("invalid_input", "POST", "/complaints", 422, "VALIDATION_ERROR",
                           json={**make_body(), "priority": "not-a-priority"})
                    created = client.post("/complaints", json=make_body(),
                                          headers={"X-Correlation-ID": "evidence-created"})
                    assert created.status_code == 201
                    record("duplicate_complaint", "POST", "/complaints", 409, "CONFLICT",
                           json=make_body())
                    record("invalid_transition", "PATCH", "/complaints/CMP999/status", 409,
                           "INVALID_STATUS_TRANSITION",
                           json={"status": "CLOSED", "changed_by": "EMP001"})
                    app.dependency_overrides[get_readiness_checker] = lambda: (lambda: False)
                    try:
                        record("unavailable_database", "GET", "/health/ready", 503,
                               "DEPENDENCY_UNAVAILABLE")
                    finally:
                        del app.dependency_overrides[get_readiness_checker]

                    class BrokenService:
                        def get_complaint(self, complaint_id):
                            raise RuntimeError("DO_NOT_EXPOSE_INTERNAL_PASSWORD")

                    app.dependency_overrides[get_complaint_service] = lambda: BrokenService()
                    record("unexpected_exception", "GET", "/complaints/CMP001", 500, "INTERNAL_ERROR")
            finally:
                app.dependency_overrides.clear()
                db.dispose()
    finally:
        LOGGER.removeHandler(captured)

    encoded = json.dumps(captured.items)
    assert "DO_NOT_LOG_MY_SENSITIVE_NARRATIVE" not in encoded
    assert "DO_NOT_EXPOSE_INTERNAL_PASSWORD" not in encoded
    assert "DB_PASSWORD" not in encoded
    (OUTPUT / "sample_logs.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in captured.items), encoding="utf-8")
    with (OUTPUT / "failure_matrix.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Captured {len(rows)} error scenarios and {len(captured.items)} safe log lines")


if __name__ == "__main__":
    main()
