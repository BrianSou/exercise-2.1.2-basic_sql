"""Plain Python fakes. Unit tests do not open a database."""
from datetime import datetime, timezone

import pytest

from src.services.complaint_service import ComplaintService

FIXED_TIME = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class FakeCustomerRepository:
    def get_by_id(self, customer_id):
        if customer_id == "CUS001":
            return {"customer_id": "CUS001", "first_name": "Test", "last_name": "Person"}
        return None


class FakeAccountRepository:
    def get_for_customer(self, customer_id):
        if customer_id == "CUS001":
            return [{"account_id": "ACC001", "customer_id": "CUS001"}]
        return []


class FakeComplaintRepository:
    def __init__(self):
        self.rows = {}
        self.events = []

    def get_by_id(self, complaint_id):
        return self.rows.get(complaint_id)

    def get_for_customer(self, customer_id):
        return [row.copy() for row in self.rows.values() if row["customer_id"] == customer_id]

    def create(self, complaint, initial_event=None):
        self.rows[complaint["complaint_id"]] = complaint.copy()
        if initial_event is not None:
            self.events.append(initial_event)
        return complaint.copy()

    def save_status_change(self, complaint_id, expected_status, new_status, event):
        row = self.rows[complaint_id]
        if row["status"] != expected_status:
            raise ValueError("Complaint status changed")
        row["status"] = new_status
        self.events.append(event)
        return row.copy()


@pytest.fixture
def service_and_repo():
    repo = FakeComplaintRepository()
    service = ComplaintService(repo, FakeCustomerRepository(), FakeAccountRepository())
    return service, repo


@pytest.fixture
def valid_new_complaint():
    return {
        "complaint_id": "CMP999", "customer_id": "CUS001",
        "category": "Fee Dispute", "priority": "High",
        "created_by": "EMP001", "received_at": FIXED_TIME,
    }
