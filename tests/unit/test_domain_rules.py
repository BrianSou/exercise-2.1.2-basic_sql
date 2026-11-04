"""3.4.1: deterministic domain and service behavior tests without persistence."""
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from src.domain.models import (
    Account, Complaint, ComplaintCategory, ComplaintPriority,
    ComplaintStatus, ComplaintStatusEvent, Customer, check_transition, as_status,
)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("from_status,to_status", [
    ("OPEN", "IN_PROGRESS"), ("OPEN", "UNDER_REVIEW"),
    ("OPEN", "ESCALATED"), ("IN_PROGRESS", "CLOSED"),
    ("UNDER_REVIEW", "IN_PROGRESS"), ("ESCALATED", "CLOSED"),
])
def test_domain_allows_documented_transition(from_status, to_status):
    check_transition(from_status, to_status)


@pytest.mark.parametrize("from_status,to_status", [
    ("OPEN", "CLOSED"), ("OPEN", "OPEN"),
    ("CLOSED", "OPEN"), ("CLOSED", "CLOSED"),
])
def test_domain_blocks_undocumented_transition(from_status, to_status):
    with pytest.raises(ValueError, match="Cannot change status"):
        check_transition(from_status, to_status)


@pytest.mark.parametrize("field,value", [
    ("complaint_id", ""), ("customer_id", " "),
    ("category", "Made Up"), ("priority", "Urgent"),
    ("received_at", "2026-11-01"),
])
def test_complaint_rejects_invalid_fields(field, value):
    options = {"complaint_id": "CMP999", "customer_id": "CUS001",
               "category": "Fee Dispute", "priority": "High", "received_at": NOW}
    options[field] = value
    with pytest.raises(ValueError):
        Complaint(**options)


def test_customer_model_requires_name():
    with pytest.raises(ValueError, match="last_name is required"):
        Customer("CUS001", "Someone", "")


def test_account_model_requires_owner():
    with pytest.raises(ValueError, match="customer_id is required"):
        Account("ACC001", "", "Savings")


def test_models_are_immutable():
    complaint = Complaint("CMP999", "CUS001", ComplaintCategory.FEE_DISPUTE, ComplaintPriority.HIGH)
    with pytest.raises(FrozenInstanceError):
        complaint.status = ComplaintStatus.CLOSED


def test_history_records_actor_and_timestamps():
    event = ComplaintStatusEvent("CMP999", "OPEN", "IN_PROGRESS", "EMP001", NOW)
    assert event.changed_by == "EMP001"
    assert event.changed_at == NOW


def test_history_cannot_claim_invalid_transition():
    with pytest.raises(ValueError, match="Cannot change status"):
        ComplaintStatusEvent("CMP999", "OPEN", "CLOSED", "EMP001", NOW)


def test_new_complaint_must_start_open():
    with pytest.raises(ValueError, match="must start as OPEN"):
        ComplaintStatusEvent("CMP999", None, "IN_PROGRESS", "EMP001", NOW)


def test_in_review_is_not_an_escalation_indicator():
    assert as_status("In Review") == ComplaintStatus.UNDER_REVIEW
    assert as_status("In Review") != ComplaintStatus.ESCALATED


@pytest.mark.parametrize("account_id", [None, "ACC001"])
def test_service_accepts_optional_or_owned_account(service_and_repo, valid_new_complaint, account_id):
    service, repo = service_and_repo
    new = service.create_complaint(**valid_new_complaint, account_id=account_id)
    assert new["account_id"] == account_id
    assert len(repo.events) == 1


def test_service_blocks_missing_customer(service_and_repo, valid_new_complaint):
    service, repo = service_and_repo
    with pytest.raises(ValueError, match="Customer not found"):
        service.create_complaint(**{**valid_new_complaint, "customer_id": "CUS404"})
    assert not repo.rows


@pytest.mark.parametrize("account_id", ["ACC404", "ACC002"])
def test_service_blocks_unowned_account(service_and_repo, valid_new_complaint, account_id):
    service, repo = service_and_repo
    with pytest.raises(ValueError, match="Account not found"):
        service.create_complaint(**valid_new_complaint, account_id=account_id)
    assert not repo.rows


def test_service_does_not_write_blocked_status_change(service_and_repo, valid_new_complaint):
    service, repo = service_and_repo
    service.create_complaint(**valid_new_complaint)
    with pytest.raises(ValueError, match="Cannot change status"):
        service.change_status("CMP999", "CLOSED", "EMP001", changed_at=NOW)
    assert repo.rows["CMP999"]["status"] == "OPEN"
    assert len(repo.events) == 1


def test_service_escalation_is_separate_from_complaint_status(service_and_repo, valid_new_complaint):
    service, repo = service_and_repo
    service.create_complaint(**valid_new_complaint)
    with pytest.raises(ValueError, match="ESCALATED is not"):
        service.change_status("CMP999", "ESCALATED", "EMP001", changed_at=NOW)
    assert repo.rows["CMP999"]["status"] == "OPEN"
    assert len(repo.events) == 1


def test_service_records_valid_transition(service_and_repo, valid_new_complaint):
    service, repo = service_and_repo
    service.create_complaint(**valid_new_complaint)
    changed = service.change_status("CMP999", "IN_PROGRESS", "EMP001", changed_at=NOW)
    assert changed["status"] == "IN_PROGRESS"
    assert (repo.events[-1].old_status.value, repo.events[-1].new_status.value) == ("OPEN", "IN_PROGRESS")
