"""Service tests. Most use fakes, so a real database is not required."""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

import pytest

from src.data.database_manager import DatabaseManager
from src.data.complaint_repository import ComplaintRepository
from src.domain.models import ComplaintStatusEvent
from src.services.complaint_service import ComplaintService
from src.services.dependencies import build_complaint_service
from legacy.build_database import seed


NOW = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)


class FakeCustomers:
    def get_by_id(self, customer_id):
        return {"customer_id": customer_id} if customer_id == "CUS001" else None


class FakeAccounts:
    def get_for_customer(self, customer_id):
        return [{"account_id": "ACC001", "customer_id": "CUS001"}] if customer_id == "CUS001" else []


class FakeComplaints:
    def __init__(self):
        self.rows = {}
        self.events = []

    def get_by_id(self, complaint_id):
        return self.rows.get(complaint_id)

    def get_for_customer(self, customer_id):
        return [r for r in self.rows.values() if r["customer_id"] == customer_id]

    def create(self, complaint, initial_event=None):
        self.rows[complaint["complaint_id"]] = complaint.copy()
        if initial_event is not None:
            self.events.append(initial_event)
        return complaint.copy()

    def save_status_change(self, complaint_id, expected_status, new_status, event):
        if self.rows[complaint_id]["status"] != expected_status:
            raise ValueError("Complaint status changed")
        self.rows[complaint_id]["status"] = new_status
        self.events.append(event)
        return self.rows[complaint_id].copy()


@pytest.fixture
def sample():
    complaints = FakeComplaints()
    service = ComplaintService(complaints, FakeCustomers(), FakeAccounts())
    return service, complaints


def create(service, **changes):
    args = dict(complaint_id="CMP999", customer_id="CUS001", category="Fee Dispute",
                priority="High", created_by="EMP001", received_at=NOW)
    args.update(changes)
    return service.create_complaint(**args)


def test_create_starts_open_and_records_first_event(sample):
    service, repo = sample
    row = create(service)
    assert row["status"] == "OPEN"
    assert row["category"] == "Fee Dispute"
    assert len(repo.events) == 1
    assert repo.events[0].old_status is None
    assert repo.events[0].new_status.value == "OPEN"


def test_create_with_optional_account(sample):
    service, _ = sample
    assert create(service, account_id=None)["account_id"] is None


def test_create_with_owned_account(sample):
    service, _ = sample
    assert create(service, account_id="ACC001")["account_id"] == "ACC001"


@pytest.mark.parametrize("bad_account", ["ACC999", "ACC002"])
def test_reject_other_customer_or_missing_account(sample, bad_account):
    service, repo = sample
    with pytest.raises(ValueError, match="Account not found"):
        create(service, account_id=bad_account)
    assert repo.rows == {}


def test_reject_missing_customer(sample):
    service, repo = sample
    with pytest.raises(ValueError, match="Customer not found"):
        create(service, customer_id="CUS404")
    assert repo.rows == {}


@pytest.mark.parametrize("field,value", [("category", "Unlisted"), ("priority", "Urgent")])
def test_reject_uncontrolled_values(sample, field, value):
    service, repo = sample
    with pytest.raises(ValueError):
        create(service, **{field: value})
    assert repo.rows == {}


def test_duplicate_id_rejected(sample):
    service, repo = sample
    create(service)
    with pytest.raises(ValueError, match="already exists"):
        create(service)
    assert len(repo.rows) == 1


def test_can_read_complaint(sample):
    service, _ = sample
    create(service)
    assert service.get_complaint("CMP999")["complaint_id"] == "CMP999"
    assert service.get_complaint("MISSING") is None


def test_can_list_customer_complaints(sample):
    service, _ = sample
    create(service)
    assert len(service.get_for_customer("CUS001")) == 1
    with pytest.raises(ValueError, match="Customer not found"):
        service.get_for_customer("CUS404")


def test_allowed_status_change_adds_event(sample):
    service, repo = sample
    create(service)
    updated = service.change_status("CMP999", "IN_PROGRESS", "EMP001", "Investigating", NOW)
    assert updated["status"] == "IN_PROGRESS"
    assert len(repo.events) == 2
    assert repo.events[-1].old_status.value == "OPEN"
    assert repo.events[-1].new_status.value == "IN_PROGRESS"


def test_invalid_status_change_keeps_original(sample):
    service, repo = sample
    create(service)
    with pytest.raises(ValueError, match="Cannot change status"):
        service.change_status("CMP999", "CLOSED", "EMP001", changed_at=NOW)
    assert repo.rows["CMP999"]["status"] == "OPEN"
    assert len(repo.events) == 1


def test_closed_cannot_reopen(sample):
    service, repo = sample
    create(service)
    service.change_status("CMP999", "IN_PROGRESS", "EMP001", changed_at=NOW)
    service.change_status("CMP999", "CLOSED", "EMP001", changed_at=NOW)
    with pytest.raises(ValueError, match="Cannot change status"):
        service.change_status("CMP999", "OPEN", "EMP001", changed_at=NOW)
    assert repo.rows["CMP999"]["status"] == "CLOSED"


def test_reject_unknown_status(sample):
    service, repo = sample
    create(service)
    with pytest.raises(ValueError, match="Unknown complaint status"):
        service.change_status("CMP999", "WAITING", "EMP001", changed_at=NOW)
    assert repo.rows["CMP999"]["status"] == "OPEN"


def test_original_schema_cannot_store_escalated_status(sample):
    service, repo = sample
    create(service)
    with pytest.raises(ValueError, match="not a complaint status"):
        service.change_status("CMP999", "ESCALATED", "EMP001", changed_at=NOW)
    assert repo.rows["CMP999"]["status"] == "OPEN"


def test_missing_complaint_cannot_change_status(sample):
    service, _ = sample
    with pytest.raises(ValueError, match="Complaint not found"):
        service.change_status("UNKNOWN", "IN_PROGRESS", "EMP001")


def test_actor_required(sample):
    service, repo = sample
    with pytest.raises(ValueError, match="changed_by"):
        create(service, created_by="")
    assert repo.rows == {}


def test_fake_repository_is_used(sample):
    service, fake_repo = sample
    create(service)
    assert service.complaints is fake_repo
    assert fake_repo.get_by_id("CMP999") is not None


@pytest.fixture
def real_db(tmp_path):
    path = tmp_path / "isolated.db"
    seed(path)
    return DatabaseManager(path)


def test_real_repository_create_and_status_history(real_db):
    service = build_complaint_service(real_db)
    created = create(service, account_id="ACC001")
    assert created["status"] == "OPEN"
    updated = service.change_status("CMP999", "IN_PROGRESS", "EMP001", "Started", NOW)
    assert updated["status"] == "IN_PROGRESS"
    with real_db.session() as session:
        history = session.execute(
            text("SELECT old_status, new_status FROM complaint_status_history "
                 "WHERE complaint_id = :id ORDER BY history_id"),
            {"id": "CMP999"},
        ).mappings().all()
        assert [(x["old_status"], x["new_status"]) for x in history] == [
            (None, "OPEN"), ("OPEN", "IN_PROGRESS")]


def test_failed_opening_event_rolls_back_complaint(real_db):
    service = build_complaint_service(real_db)
    with pytest.raises(IntegrityError):
        create(service, created_by="EMP_DOES_NOT_EXIST")
    assert service.get_complaint("CMP999") is None


def test_failed_status_event_rolls_back_status(real_db):
    service = build_complaint_service(real_db)
    create(service)
    with pytest.raises(IntegrityError):
        service.change_status("CMP999", "IN_PROGRESS", "EMP_DOES_NOT_EXIST", changed_at=NOW)
    assert service.get_complaint("CMP999")["status"] == "OPEN"
    with real_db.session() as session:
        count = session.execute(
            text("SELECT COUNT(*) FROM complaint_status_history WHERE complaint_id = :id"),
            {"id": "CMP999"},
        ).scalar_one()
        assert count == 1  # only the initial OPEN event remains


def test_wrong_expected_status_does_not_overwrite_change(real_db):
    service = build_complaint_service(real_db)
    create(service)
    # Simulate another request changing the record after it was read.
    with pytest.raises(ValueError, match="status changed"):
        event = ComplaintStatusEvent("CMP999", "UNDER_REVIEW", "IN_PROGRESS", "EMP001", NOW)
        ComplaintRepository(real_db).save_status_change(
            "CMP999", "UNDER_REVIEW", "IN_PROGRESS", event)
    assert service.get_complaint("CMP999")["status"] == "OPEN"


def test_existing_repositories_still_work(real_db):
    service = build_complaint_service(real_db)
    assert service.get_complaint("CMP001")["category"] == "Fee Dispute"
    assert service.get_for_customer("CUS001")
