"""Optional development setup for testing the API with PostgreSQL.

Run only on an empty training database. This imports the original Week 2 CSVs
into the four tables used by the API. It does not reset or delete records.
"""

import argparse
import csv
from decimal import Decimal
from pathlib import Path

from sqlalchemy import insert, select

from src.data.orm_models import (
    Base, CustomerRow, AccountRow, ComplaintRow, ComplaintStatusEventRow,
)
from src.dependencies import get_engine

DATA_DIR = Path(__file__).resolve().parents[2] / "legacy" / "data"


def read_rows(name, folder):
    with (folder / f"{name}.csv").open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def seed_demo(engine, folder=DATA_DIR):
    """Create missing ORM tables and insert sample records only if all are empty."""
    customers = read_rows("customer", folder)
    accounts = read_rows("account", folder)
    complaints = read_rows("complaint", folder)
    events = read_rows("complaint_status_history", folder)

    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        for model in (CustomerRow, AccountRow, ComplaintRow, ComplaintStatusEventRow):
            if connection.scalar(select(model).limit(1)) is not None:
                raise ValueError("Training tables contain data. No rows were changed.")

        connection.execute(insert(CustomerRow), [
            {"customer_id": row["customer_id"], "first_name": row["first_name"],
             "last_name": row["last_name"], "email": row["email"] or None}
            for row in customers
        ])
        connection.execute(insert(AccountRow), [
            {"account_id": row["account_id"], "customer_id": row["customer_id"],
             "account_type": row["account_type"] or None, "status": row["status"] or None,
             "current_balance": Decimal(row["current_balance"]) if row["current_balance"] else None}
            for row in accounts
        ])
        connection.execute(insert(ComplaintRow), [
            {"complaint_id": row["complaint_id"], "customer_id": row["customer_id"],
             "account_id": row["account_id"] or None, "channel": row["channel"] or None,
             "category": row["category"], "complaint_text": row["complaint_text"] or None,
             "priority": row["priority"] or None, "status": row["status"],
             "received_at": row["received_at"],
             "assigned_analyst_id": row["assigned_analyst_id"] or None}
            for row in complaints
        ])
        connection.execute(insert(ComplaintStatusEventRow), [
            {"history_id": int(row["history_id"]), "complaint_id": row["complaint_id"],
             "old_status": row["old_status"] or None, "new_status": row["new_status"],
             "changed_by": row["changed_by"], "changed_at": row["changed_at"],
             "comments": row["comments"] or None}
            for row in events
        ])
        # The existing Week 2 history IDs are explicit. On PostgreSQL the
        # identity sequence must continue after the highest imported value.
        if engine.dialect.name == "postgresql":
            from sqlalchemy import text
            connection.execute(text("SELECT setval(pg_get_serial_sequence(" 
                "'complaint_status_history', 'history_id'), "
                "(SELECT MAX(history_id) FROM complaint_status_history))"))

    return {"customers": len(customers), "accounts": len(accounts),
            "complaints": len(complaints), "history_events": len(events)}


def main():
    parser = argparse.ArgumentParser(description="Set up example PostgreSQL API data")
    parser.add_argument("--seed", action="store_true",
                        help="Confirm you want to create tables and import demo data")
    options = parser.parse_args()
    if not options.seed:
        parser.error("Nothing changed. Use --seed to initialize empty training tables.")
    result = seed_demo(get_engine())
    print("Demo data loaded:", result)


if __name__ == "__main__":
    main()
