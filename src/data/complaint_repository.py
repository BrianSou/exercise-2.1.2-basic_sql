"""Complaint persistence with SQLAlchemy ORM.

The repository does not decide whether a transition is permitted. The service
and domain handle that. Writes and history events share one transaction.
"""

from datetime import datetime
from sqlalchemy import select, update

from src.data.orm_models import ComplaintRow, ComplaintStatusEventRow

COLUMNS = (
    "complaint_id", "customer_id", "account_id", "channel", "category",
    "complaint_text", "priority", "status", "received_at", "assigned_analyst_id",
)


def as_dict(row):
    return {name: getattr(row, name) for name in COLUMNS}


def event_row(event):
    return ComplaintStatusEventRow(
        complaint_id=event.complaint_id,
        old_status=event.old_status.value if event.old_status else None,
        new_status=event.new_status.value,
        changed_by=event.changed_by,
        changed_at=event.changed_at.isoformat(sep=" ", timespec="seconds"),
        comments=event.comments,
    )


class ComplaintRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, complaint_id):
        with self.db.session() as session:
            row = session.get(ComplaintRow, complaint_id)
            return as_dict(row) if row else None

    def get_for_customer(self, customer_id):
        with self.db.session() as session:
            rows = session.scalars(
                select(ComplaintRow)
                .where(ComplaintRow.customer_id == customer_id)
                .order_by(ComplaintRow.complaint_id)
            ).all()
            return [as_dict(row) for row in rows]

    def create(self, complaint, initial_event=None):
        missing = [name for name in COLUMNS if name not in complaint]
        if missing:
            raise ValueError("Missing fields: " + ", ".join(missing))
        if initial_event is not None and initial_event.complaint_id != complaint["complaint_id"]:
            raise ValueError("History event does not match complaint")

        # The service always passes an opening event for new complaints.
        # One session covers both INSERTs, so either both save or neither does.
        with self.db.session() as session:
            row = ComplaintRow(**{name: complaint[name] for name in COLUMNS})
            session.add(row)
            session.flush()  # First INSERT. This does not commit.

            if initial_event is not None:
                session.add(event_row(initial_event))
                session.flush()  # Second INSERT. Failure rolls back the first.

            result = as_dict(row)
        # DatabaseManager commits only after the whole with-block succeeds.
        return result

    def save_status_change(self, complaint_id, expected_status, new_status, event):
        if (
            event.complaint_id != complaint_id
            or event.old_status is None
            or event.old_status.value != expected_status
            or event.new_status.value != new_status
        ):
            raise ValueError("History event does not match status change")

        with self.db.session() as session:
            changed = session.execute(
                update(ComplaintRow)
                .where(ComplaintRow.complaint_id == complaint_id)
                .where(ComplaintRow.status == expected_status)
                .values(status=new_status)
            )
            if changed.rowcount != 1:
                raise ValueError("Complaint status changed. Read it again and retry")
            session.add(event_row(event))
            session.flush()
            row = session.get(ComplaintRow, complaint_id)
            result = as_dict(row)
        return result
