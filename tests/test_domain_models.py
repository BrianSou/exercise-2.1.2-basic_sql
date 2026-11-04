"""Exercise 3.1.1 tests. Run: python -m pytest tests/test_domain_models.py -v"""

from datetime import datetime
from decimal import Decimal

import pytest

from src.domain.models import (
    Account, Complaint, ComplaintCategory, ComplaintPriority,
    ComplaintStatus, ComplaintStatusEvent, Customer, VALID_TRANSITIONS,
    check_transition,
)

NOW = datetime(2026, 10, 29, 9, 0)


def sample_complaint(**changes):
    values = {
        "complaint_id": "CMP001",
        "customer_id": "CUS001",
        "account_id": None,
        "category": "Fee Dispute",
        "priority": "High",
        "status": "OPEN",
    }
    values.update(changes)
    return Complaint(**values)


def test_customer_and_account():
    customer = Customer("CUS001", "William", "Johnson")
    account = Account("ACC001", "CUS001", "Chequing", current_balance=Decimal("25.50"))
    assert customer.customer_id == account.customer_id
    assert account.current_balance == Decimal("25.50")


@pytest.mark.parametrize("field", ["customer_id", "first_name", "last_name"])
def test_customer_requires_fields(field):
    values = {"customer_id": "CUS001", "first_name": "William", "last_name": "Johnson"}
    values[field] = " "
    with pytest.raises(ValueError, match="required"):
        Customer(**values)


def test_account_requires_customer():
    with pytest.raises(ValueError, match="customer_id"):
        Account("ACC001", "", "Savings")


def test_account_balance_uses_decimal():
    with pytest.raises(ValueError, match="Decimal"):
        Account("ACC001", "CUS001", "Savings", current_balance=1.2)


def test_complaint_accepts_valid_values_and_optional_account():
    complaint = sample_complaint()
    assert complaint.category == ComplaintCategory.FEE_DISPUTE
    assert complaint.priority == ComplaintPriority.HIGH
    assert complaint.status == ComplaintStatus.OPEN
    assert complaint.account_id is None


@pytest.mark.parametrize("bad_category", ["Made Up Category", "", None])
def test_reject_unknown_category(bad_category):
    with pytest.raises(ValueError, match="category"):
        sample_complaint(category=bad_category)


@pytest.mark.parametrize("bad_priority", ["Urgent", "", None])
def test_reject_unknown_priority(bad_priority):
    with pytest.raises(ValueError, match="priority"):
        sample_complaint(priority=bad_priority)


def test_reject_unknown_status():
    with pytest.raises(ValueError, match="status"):
        sample_complaint(status="WAITING")


def test_bulk_dataset_status_names_are_recognized():
    complaint = sample_complaint(category="Mortgage Servicing", status="In Review")
    assert complaint.category == ComplaintCategory.MORTGAGE_SERVICING
    assert complaint.status == ComplaintStatus.UNDER_REVIEW
    assert sample_complaint(status="Escalated").status == ComplaintStatus.ESCALATED


@pytest.mark.parametrize("old,new", [
    ("OPEN", "IN_PROGRESS"),
    ("OPEN", "UNDER_REVIEW"),
    ("IN_PROGRESS", "CLOSED"),
    ("UNDER_REVIEW", "CLOSED"),
    ("ESCALATED", "IN_PROGRESS"),
])
def test_valid_transitions(old, new):
    check_transition(old, new)


@pytest.mark.parametrize("old,new", [
    ("OPEN", "CLOSED"),
    ("CLOSED", "OPEN"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("UNDER_REVIEW", "OPEN"),
])
def test_invalid_transitions(old, new):
    with pytest.raises(ValueError, match="Cannot change status"):
        check_transition(old, new)


def test_closed_status_has_no_next_step():
    assert VALID_TRANSITIONS[ComplaintStatus.CLOSED] == set()


def test_first_event_must_open_complaint():
    check_transition(None, "OPEN")
    with pytest.raises(ValueError, match="must start as OPEN"):
        check_transition(None, "CLOSED")


def test_status_change_returns_new_complaint_and_event():
    original = sample_complaint()
    changed, event = original.change_status("IN_PROGRESS", "EMP001", NOW, "Assigned")
    assert original.status == ComplaintStatus.OPEN  # the original is unchanged
    assert changed.status == ComplaintStatus.IN_PROGRESS
    assert event.old_status == ComplaintStatus.OPEN
    assert event.new_status == ComplaintStatus.IN_PROGRESS
    assert event.complaint_id == original.complaint_id
    assert event.changed_by == "EMP001"


def test_status_event_rejects_invalid_change():
    with pytest.raises(ValueError, match="Cannot change status"):
        ComplaintStatusEvent("CMP001", "CLOSED", "IN_PROGRESS", "EMP001", NOW)


def test_status_event_requires_actor_and_timestamp():
    with pytest.raises(ValueError, match="changed_by"):
        ComplaintStatusEvent("CMP001", "OPEN", "IN_PROGRESS", "", NOW)
    with pytest.raises(ValueError, match="changed_at"):
        ComplaintStatusEvent("CMP001", "OPEN", "IN_PROGRESS", "EMP001", "today")


def test_account_id_cannot_be_blank():
    with pytest.raises(ValueError, match="account_id"):
        sample_complaint(account_id="")
