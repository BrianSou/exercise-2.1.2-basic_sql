"""Run a small service demo without changing the training database."""
import tempfile
from pathlib import Path
from legacy.build_database import seed
from src.data.database_manager import DatabaseManager
from src.services.dependencies import build_complaint_service


def main():
    with tempfile.TemporaryDirectory() as folder:
        db_path = Path(folder) / "practice.db"
        seed(db_path)
        service = build_complaint_service(DatabaseManager(db_path))

        created = service.create_complaint(
            "CMP999", "CUS001", "Fee Dispute", "High", "EMP001",
            account_id="ACC001", complaint_text="Incorrect fee",
        )
        print("Created:", created["complaint_id"], created["status"])
        updated = service.change_status(
            "CMP999", "IN_PROGRESS", "EMP001", "Investigation started"
        )
        print("Updated:", updated["complaint_id"], updated["status"])
        print("Original database was not modified.")


if __name__ == "__main__":
    main()
