"""Simple models for the banking complaint project.

These classes describe the data and enforce basic rules.
They do not read or write the database.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ComplaintCategory(str, Enum):
    # Categories in the original 30-complaint database.
    FEE_DISPUTE = "Fee Dispute"
    SERVICE_DELAY = "Service Delay"
    TRANSACTION_ERROR = "Transaction Error"
    ONLINE_BANKING = "Online Banking"
    CARD_ISSUE = "Card Issue"
    CUSTOMER_SERVICE = "Customer Service"
    FRAUD_CLAIM = "Fraud Claim"

    # Categories in the separate 120-complaint dataset.
    CARD_OR_TRANSACTION_DISPUTE = "Card or Transaction Dispute"
    MORTGAGE_SERVICING = "Mortgage Servicing"
    SERVICE_QUALITY = "Service Quality"
    ACCOUNT_ACCESS = "Account Access"
    FEES = "Fees"
    DIGITAL_BANKING = "Digital Banking"


class ComplaintPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ComplaintStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    UNDER_REVIEW = "UNDER_REVIEW"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


# The bulk CSV uses different labels for some statuses.
BULK_STATUS_NAMES = {
    "Open": ComplaintStatus.OPEN,
    "In Review": ComplaintStatus.UNDER_REVIEW,
    "Escalated": ComplaintStatus.ESCALATED,
    "Closed": ComplaintStatus.CLOSED,
}


def as_status(value: ComplaintStatus | str) -> ComplaintStatus:
    if isinstance(value, ComplaintStatus):
        return value
    if isinstance(value, str) and value in BULK_STATUS_NAMES:
        return BULK_STATUS_NAMES[value]
    try:
        return ComplaintStatus(value)
    except (ValueError, TypeError):
        raise ValueError(f"Unknown complaint status: {value!r}") from None


def required(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")


# These are proposed workflow rules. The Week 3 brief does not set them.
VALID_TRANSITIONS = {
    ComplaintStatus.OPEN: {
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.ESCALATED,
    },
    ComplaintStatus.IN_PROGRESS: {
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.CLOSED,
    },
    ComplaintStatus.UNDER_REVIEW: {
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.CLOSED,
    },
    ComplaintStatus.ESCALATED: {
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.CLOSED,
    },
    ComplaintStatus.CLOSED: set(),
}


def check_transition(old_status: ComplaintStatus | str | None,
                     new_status: ComplaintStatus | str) -> None:
    new = as_status(new_status)
    if old_status is None:
        if new != ComplaintStatus.OPEN:
            raise ValueError("A new complaint must start as OPEN")
        return
    old = as_status(old_status)
    if new not in VALID_TRANSITIONS[old]:
        raise ValueError(f"Cannot change status from {old.value} to {new.value}")


@dataclass(frozen=True)
class Customer:
    customer_id: str
    first_name: str
    last_name: str
    email: str | None = None

    def __post_init__(self):
        required(self.customer_id, "customer_id")
        required(self.first_name, "first_name")
        required(self.last_name, "last_name")


@dataclass(frozen=True)
class Account:
    account_id: str
    customer_id: str
    account_type: str
    status: str = "ACTIVE"
    current_balance: Decimal | None = None

    def __post_init__(self):
        required(self.account_id, "account_id")
        required(self.customer_id, "customer_id")
        required(self.account_type, "account_type")
        required(self.status, "status")
        if self.current_balance is not None and not isinstance(self.current_balance, Decimal):
            raise ValueError("current_balance must be a Decimal")


@dataclass(frozen=True)
class Complaint:
    complaint_id: str
    customer_id: str
    category: ComplaintCategory | str
    priority: ComplaintPriority | str
    status: ComplaintStatus | str = ComplaintStatus.OPEN
    account_id: str | None = None
    received_at: datetime | None = None

    def __post_init__(self):
        required(self.complaint_id, "complaint_id")
        required(self.customer_id, "customer_id")
        if self.account_id is not None:
            required(self.account_id, "account_id")
        try:
            category = ComplaintCategory(self.category)
        except (ValueError, TypeError):
            raise ValueError(f"Unknown complaint category: {self.category!r}") from None
        try:
            priority = ComplaintPriority(self.priority)
        except (ValueError, TypeError):
            raise ValueError(f"Unknown complaint priority: {self.priority!r}") from None
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "priority", priority)
        object.__setattr__(self, "status", as_status(self.status))
        if self.received_at is not None and not isinstance(self.received_at, datetime):
            raise ValueError("received_at must be a datetime")

    def change_status(self, new_status: ComplaintStatus | str, changed_by: str,
                      changed_at: datetime, comments: str | None = None):
        """Return the updated complaint and a record of the change."""
        event = ComplaintStatusEvent(
            complaint_id=self.complaint_id,
            old_status=self.status,
            new_status=new_status,
            changed_by=changed_by,
            changed_at=changed_at,
            comments=comments,
        )
        updated = replace(self, status=event.new_status)
        return updated, event


@dataclass(frozen=True)
class ComplaintStatusEvent:
    complaint_id: str
    old_status: ComplaintStatus | str | None
    new_status: ComplaintStatus | str
    changed_by: str
    changed_at: datetime
    comments: str | None = None
    history_id: int | None = None

    def __post_init__(self):
        required(self.complaint_id, "complaint_id")
        required(self.changed_by, "changed_by")
        if not isinstance(self.changed_at, datetime):
            raise ValueError("changed_at must be a datetime")
        if self.history_id is not None and (
            not isinstance(self.history_id, int) or self.history_id <= 0
        ):
            raise ValueError("history_id must be a positive number")
        old = as_status(self.old_status) if self.old_status is not None else None
        new = as_status(self.new_status)
        check_transition(old, new)
        object.__setattr__(self, "old_status", old)
        object.__setattr__(self, "new_status", new)
