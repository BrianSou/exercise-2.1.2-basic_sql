"""3.1.1/3.1.2 checks using SQLAlchemy with an isolated database."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from legacy.build_database import seed
from src.data.database_manager import DatabaseManager
from src.data.orm_models import Base, CustomerRow, AccountRow, ComplaintRow, ComplaintStatusEventRow
from src.data.customer_repository import CustomerRepository
from src.data.account_repository import AccountRepository
from src.data.complaint_repository import ComplaintRepository
from src.services.dependencies import build_complaint_service

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    seed(path)
    manager = DatabaseManager(path)
    yield manager
    manager.dispose()


def test_mappings_have_original_table_names():
    assert Base.metadata.tables.keys() >= {
        "customer", "account", "complaint", "complaint_status_history"
    }


def test_reads_real_week2_data(db):
    assert CustomerRepository(db).get_by_id("CUS001")["first_name"]
    assert AccountRepository(db).get_for_customer("CUS001")
    assert ComplaintRepository(db).get_by_id("CMP001")["status"] == "OPEN"
    with db.session() as session:
        assert session.get(CustomerRow, "CUS001") is not None
        assert session.scalars(select(ComplaintRow)).all()


def test_sqlalchemy_uses_bound_parameters(db):
    assert CustomerRepository(db).get_by_id("CUS001' OR 1=1 --") is None


def test_create_is_atomic_with_opening_event(db):
    service = build_complaint_service(db)
    service.create_complaint("CMP900", "CUS001", "Fee Dispute", "High", "EMP001", received_at=NOW)
    with db.session() as session:
        assert session.get(ComplaintRow, "CMP900") is not None
        events = session.scalars(select(ComplaintStatusEventRow).where(
            ComplaintStatusEventRow.complaint_id == "CMP900"
        )).all()
        assert len(events) == 1
        assert events[0].new_status == "OPEN"


def test_failed_initial_event_rolls_back_creation(db):
    service = build_complaint_service(db)
    with pytest.raises(IntegrityError):
        service.create_complaint("CMP901", "CUS001", "Fee Dispute", "High", "NONEXISTENT", received_at=NOW)
    assert service.get_complaint("CMP901") is None


def test_failed_history_rolls_back_update(db):
    service = build_complaint_service(db)
    service.create_complaint("CMP902", "CUS001", "Fee Dispute", "High", "EMP001", received_at=NOW)
    with pytest.raises(IntegrityError):
        service.change_status("CMP902", "IN_PROGRESS", "NONEXISTENT", changed_at=NOW)
    assert service.get_complaint("CMP902")["status"] == "OPEN"
    with db.session() as session:
        events = session.scalars(select(ComplaintStatusEventRow).where(
            ComplaintStatusEventRow.complaint_id == "CMP902"
        )).all()
        assert len(events) == 1


def test_session_is_rolled_back_after_integrity_error(db):
    with pytest.raises(IntegrityError):
        with db.session() as session:
            session.add(CustomerRow(customer_id="CUS001", first_name="Duplicated", last_name="Customer"))
            session.flush()
    # A new session is still usable after the exception.
    assert CustomerRepository(db).get_by_id("CUS001") is not None


def test_foreign_keys_are_enforced(db):
    with pytest.raises(IntegrityError):
        with db.session() as session:
            session.add(AccountRow(account_id="ACC999", customer_id="MISSING", account_type="Savings"))
            session.flush()


def test_database_manager_closes_connection_after_exception(db):
    with pytest.raises(RuntimeError):
        with db.session() as session:
            session.execute(text("SELECT 1"))
            raise RuntimeError("stop")
    with db.session() as session:
        assert session.scalar(text("SELECT 1")) == 1
