"""Run the seeder in a temporary folder so the real data stays untouched."""

import csv
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import seed_database


class SeederTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        for name in ["customers.csv", "accounts.csv", "complaints.csv",
                     "service_requests.csv", "starter_database.sql"]:
            shutil.copy(ROOT / "data" / name, self.folder / name)
        self.db = self.folder / "test.db"

    def run_seed(self, *options):
        return subprocess.run(
            [sys.executable, str(ROOT / "seed_database.py"),
             "--data-dir", str(self.folder), "--db", str(self.db), *options],
            capture_output=True, text=True,
        )

    def change_row(self, name, row_index, field, value):
        path = self.folder / name
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns, rows = reader.fieldnames, list(reader)
        rows[row_index][field] = value
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    def row_count(self, table):
        with sqlite3.connect(self.db) as db:
            return db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]

    def test_first_run(self):
        result = self.run_seed()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.row_count("customers"), 100)
        self.assertEqual(self.row_count("accounts"), 150)
        self.assertEqual(self.row_count("complaints"), 120)
        self.assertEqual(self.row_count("service_requests"), 5)
        self.assertIn("Result: PASS", (self.folder / "integrity_report.txt").read_text())
        with (self.folder / "rejected_rows.csv").open(newline="", encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 0)

    def test_second_run_needs_reset(self):
        self.assertEqual(self.run_seed().returncode, 0)
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertEqual(self.row_count("customers"), 100)
        self.assertIn("rolled back", (self.folder / "seed_run_log.txt").read_text())

    def test_reset(self):
        self.assertEqual(self.run_seed().returncode, 0)
        with sqlite3.connect(self.db) as db:
            db.execute("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)",
                       ("EXTRA", "A", "B", "Standard", "Low", "example@test"))
        self.assertEqual(self.row_count("customers"), 101)
        self.assertEqual(self.run_seed("--reset").returncode, 0)
        self.assertEqual(self.row_count("customers"), 100)

    def test_missing_file(self):
        (self.folder / "accounts.csv").unlink()
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Missing file", (self.folder / "rejected_rows.csv").read_text())
        self.assertFalse(self.db.exists())

    def test_missing_header(self):
        path = self.folder / "customers.csv"
        path.write_text(path.read_text().replace("first_name", "name", 1))
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Missing columns: first_name", (self.folder / "rejected_rows.csv").read_text())

    def test_duplicate_id(self):
        self.change_row("customers.csv", 1, "customer_id", "C0001")
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Duplicate customer_id", (self.folder / "rejected_rows.csv").read_text())

    def test_missing_customer(self):
        self.change_row("accounts.csv", 0, "customer_id", "UNKNOWN")
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Customer does not exist", (self.folder / "rejected_rows.csv").read_text())

    def test_wrong_account_owner(self):
        self.change_row("complaints.csv", 0, "customer_id", "C0001")
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Account belongs to another customer", (self.folder / "rejected_rows.csv").read_text())

    def test_missing_account(self):
        self.change_row("complaints.csv", 0, "account_id", "UNKNOWN")
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Account does not exist", (self.folder / "rejected_rows.csv").read_text())

    def test_bad_date(self):
        self.change_row("complaints.csv", 0, "date_opened", "not-a-date")
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Invalid date_opened date", (self.folder / "rejected_rows.csv").read_text())

    def test_request_customer_mismatch(self):
        self.change_row("service_requests.csv", 0, "customer_id", "C0001")
        self.assertNotEqual(self.run_seed().returncode, 0)
        self.assertIn("Customer does not match complaint", (self.folder / "rejected_rows.csv").read_text())

    def test_blank_optional_account(self):
        self.assertEqual(self.run_seed().returncode, 0)
        with sqlite3.connect(self.db) as db:
            count = db.execute("SELECT COUNT(*) FROM complaints WHERE account_id IS NULL").fetchone()[0]
        self.assertEqual(count, 39)

    def test_failure_after_insert_rolls_back_reset(self):
        self.assertEqual(self.run_seed().returncode, 0)
        with sqlite3.connect(self.db) as db:
            db.execute("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)",
                       ("EXTRA", "A", "B", "Standard", "Low", "example@test"))
        self.assertEqual(self.row_count("customers"), 101)
        args = type("Args", (), {"data_dir": str(self.folder), "db": str(self.db),
                                 "backend": "sqlite", "reset": True})()
        # Simulate an integrity check error after all INSERT statements run.
        with patch.object(seed_database, "check_integrity", side_effect=seed_database.SeedError("test failure")):
            self.assertEqual(seed_database.run(args), 1)
        self.assertEqual(self.row_count("customers"), 101)
        self.assertIn("rolled back", (self.folder / "seed_run_log.txt").read_text())


if __name__ == "__main__":
    unittest.main()
