"""Complaint business rules. Database queries belong in repositories."""

from datetime import datetime, timezone

from src.domain.models import Complaint, ComplaintStatus, ComplaintStatusEvent, as_status


class ComplaintService:
    def __init__(self, complaint_repo, customer_repo, account_repo):
        # Passing repositories in lets us replace them with fakes in tests.
        self.complaints = complaint_repo
        self.customers = customer_repo
        self.accounts = account_repo

    def get_customer(self, customer_id):
        """Look up a customer through the customer repository."""
        return self.customers.get_by_id(customer_id)

    def get_complaint(self, complaint_id):
        return self.complaints.get_by_id(complaint_id)

    def get_for_customer(self, customer_id):
        if self.customers.get_by_id(customer_id) is None:
            raise ValueError("Customer not found")
        return self.complaints.get_for_customer(customer_id)

    def create_complaint(self, complaint_id, customer_id, category, priority, created_by,
                         account_id=None, complaint_text="", channel="Web",
                         assigned_analyst_id=None, received_at=None):
        """Validate a new complaint and save it with an opening status event."""
        if self.customers.get_by_id(customer_id) is None:
            raise ValueError("Customer not found")
        if self.complaints.get_by_id(complaint_id) is not None:
            raise ValueError("Complaint ID already exists")
        self._check_account(customer_id, account_id)

        received_at = received_at or datetime.now(timezone.utc)
        complaint = Complaint(
            complaint_id=complaint_id,
            customer_id=customer_id,
            account_id=account_id,
            category=category,
            priority=priority,
            status=ComplaintStatus.OPEN,
            received_at=received_at,
        )
        event = ComplaintStatusEvent(
            complaint_id=complaint_id,
            old_status=None,
            new_status=ComplaintStatus.OPEN,
            changed_by=created_by,
            changed_at=received_at,
            comments="Complaint created",
        )
        row = {
            "complaint_id": complaint.complaint_id,
            "customer_id": complaint.customer_id,
            "account_id": complaint.account_id,
            "channel": channel,
            "category": complaint.category.value,
            "complaint_text": complaint_text,
            "priority": complaint.priority.value,
            "status": complaint.status.value,
            "received_at": received_at.isoformat(sep=" ", timespec="seconds"),
            "assigned_analyst_id": assigned_analyst_id,
        }
        return self.complaints.create(row, initial_event=event)

    def change_status(self, complaint_id, new_status, changed_by, comments=None,
                      changed_at=None):
        """Check the transition and save status + history in one transaction."""
        row = self.complaints.get_by_id(complaint_id)
        if row is None:
            raise ValueError("Complaint not found")

        new_status = as_status(new_status)
        if new_status == ComplaintStatus.ESCALATED:
            # Original SQLite schema stores escalation in review_decision,
            # not as a value in the complaint.status column.
            raise ValueError("ESCALATED is not a complaint status in this database")

        complaint = Complaint(
            complaint_id=row["complaint_id"],
            customer_id=row["customer_id"],
            account_id=row["account_id"],
            category=row["category"],
            priority=row["priority"],
            status=row["status"],
        )
        changed_at = changed_at or datetime.now(timezone.utc)
        updated, event = complaint.change_status(new_status, changed_by, changed_at, comments)
        return self.complaints.save_status_change(
            complaint_id, expected_status=complaint.status.value,
            new_status=updated.status.value, event=event,
        )

    def _check_account(self, customer_id, account_id):
        if account_id is None:
            return
        customer_accounts = self.accounts.get_for_customer(customer_id)
        if not any(account["account_id"] == account_id for account in customer_accounts):
            raise ValueError("Account not found for this customer")
