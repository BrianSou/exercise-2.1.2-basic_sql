"""Create the training database and load the supplied CSV data."""

import argparse
import csv
import os
import re
import sqlite3
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent

# The columns match starter_database.sql.
COLUMNS = {
    "customers": ["customer_id", "first_name", "last_name", "segment", "risk_category", "email"],
    "accounts": ["account_id", "customer_id", "account_type", "status", "current_balance"],
    "complaints": ["complaint_id", "customer_id", "account_id", "category", "status",
                   "date_opened", "date_closed", "channel", "priority"],
    "service_requests": ["request_id", "complaint_id", "customer_id", "request_type",
                         "status", "created_date"],
}

# These fields cannot be blank in the schema.
REQUIRED = {
    "customers": ["customer_id", "first_name", "last_name", "segment", "risk_category"],
    "accounts": ["account_id", "customer_id", "account_type", "status"],
    "complaints": ["complaint_id", "customer_id", "category", "status", "date_opened"],
    "service_requests": ["request_id", "created_date"],
}
KEYS = {"customers": "customer_id", "accounts": "account_id",
        "complaints": "complaint_id", "service_requests": "request_id"}
FILES = {name: name + ".csv" for name in COLUMNS}
TABLES = list(COLUMNS)


class SeedError(Exception):
    pass


def check_date(value):
    if value:
        date.fromisoformat(value)


def load_csvs(folder):
    """Read the files and collect problems before opening the database."""
    data = {}
    problems = []

    for table, filename in FILES.items():
        path = folder / filename
        if not path.is_file():
            problems.append((filename, "-", "Missing file"))
            continue

        try:
            with path.open(newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                missing = [col for col in COLUMNS[table] if col not in (reader.fieldnames or [])]
                if missing:
                    problems.append((filename, "header", "Missing columns: " + ", ".join(missing)))
                    continue

                data[table] = []
                seen = set()
                for line, raw in enumerate(reader, start=2):
                    row = {col: (raw.get(col) or "").strip() for col in COLUMNS[table]}
                    row_errors = []
                    if None in raw:  # Too many fields in a row
                        row_errors.append("Extra CSV values")
                    for col in REQUIRED[table]:
                        if not row[col]:
                            row_errors.append("Blank " + col)

                    key = row[KEYS[table]]
                    if key in seen:
                        row_errors.append("Duplicate " + KEYS[table] + ": " + key)
                    seen.add(key)

                    for col in ("date_opened", "date_closed", "created_date"):
                        if col in row:
                            try:
                                check_date(row[col])
                            except ValueError:
                                row_errors.append("Invalid " + col + " date")

                    if table == "complaints" and row["date_closed"] and row["date_opened"]:
                        if row["date_closed"] < row["date_opened"]:
                            row_errors.append("Closed date is before opened date")
                    if table == "accounts" and row["current_balance"]:
                        try:
                            amount = Decimal(row["current_balance"])
                            if not amount.is_finite() or amount.as_tuple().exponent < -2:
                                raise InvalidOperation()
                        except InvalidOperation:
                            row_errors.append("Invalid current_balance")

                    for problem in row_errors:
                        problems.append((filename, str(line), problem))
                    data[table].append(row)
        except (OSError, UnicodeError, csv.Error) as error:
            problems.append((filename, "-", "Could not read CSV: " + type(error).__name__))

    if len(data) != len(TABLES):
        return data, problems

    customers = {r["customer_id"] for r in data["customers"]}
    accounts = {r["account_id"]: r["customer_id"] for r in data["accounts"]}
    complaints = {r["complaint_id"]: r["customer_id"] for r in data["complaints"]}

    for i, row in enumerate(data["accounts"], start=2):
        if row["customer_id"] not in customers:
            problems.append(("accounts.csv", str(i), "Customer does not exist"))

    for i, row in enumerate(data["complaints"], start=2):
        if row["customer_id"] not in customers:
            problems.append(("complaints.csv", str(i), "Customer does not exist"))
        account = row["account_id"]
        if account and account not in accounts:
            problems.append(("complaints.csv", str(i), "Account does not exist"))
        elif account and accounts[account] != row["customer_id"]:
            problems.append(("complaints.csv", str(i), "Account belongs to another customer"))

    for i, row in enumerate(data["service_requests"], start=2):
        if row["customer_id"] and row["customer_id"] not in customers:
            problems.append(("service_requests.csv", str(i), "Customer does not exist"))
        complaint_id = row["complaint_id"]
        if complaint_id and complaint_id not in complaints:
            problems.append(("service_requests.csv", str(i), "Complaint does not exist"))
        elif complaint_id and row["customer_id"] and complaints[complaint_id] != row["customer_id"]:
            problems.append(("service_requests.csv", str(i), "Customer does not match complaint"))

    return data, problems


def schema_statements(path, backend):
    """Use the CREATE TABLE statements, not the partial INSERT statements."""
    script = path.read_text(encoding="utf-8")
    statements = re.findall(r"CREATE\s+TABLE\s+[^;]+;", script, flags=re.IGNORECASE)
    if len(statements) != 5:
        raise SeedError("Expected five CREATE TABLE statements in starter_database.sql")
    if backend == "sqlite":
        statements = [s.replace("status_event_id SERIAL PRIMARY KEY",
                                "status_event_id INTEGER PRIMARY KEY AUTOINCREMENT")
                      for s in statements]
    return statements


def connect(backend, db_path):
    if backend == "sqlite":
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    # PostgreSQL uses the same environment variables as Exercise 2.4.2.
    needed = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [name for name in needed if not os.getenv(name)]
    if missing:
        raise SeedError("Missing environment settings: " + ", ".join(missing))
    try:
        import psycopg2
    except ImportError:
        raise SeedError("For PostgreSQL, install the driver: pip install -r requirements.txt") from None
    try:
        return psycopg2.connect(host=os.environ["DB_HOST"], port=os.environ["DB_PORT"],
                                dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
                                password=os.environ["DB_PASSWORD"], connect_timeout=5)
    except psycopg2.Error:
        raise SeedError("Could not connect to PostgreSQL. Check your database settings.") from None


def query(cursor, sql, values, backend):
    # PostgreSQL uses %s. SQLite uses ?.
    if backend == "sqlite":
        sql = sql.replace("%s", "?")
    return cursor.execute(sql, values)


def check_integrity(cursor, expected):
    lines = []
    for table in TABLES:
        cursor.execute("SELECT COUNT(*) FROM " + table)
        actual = cursor.fetchone()[0]
        lines.append(f"{table}: {actual} loaded / {expected[table]} in CSV")
        if actual != expected[table]:
            raise SeedError("Row count does not match for " + table)

    checks = {
        "Accounts with missing customers": "SELECT COUNT(*) FROM accounts a LEFT JOIN customers c ON a.customer_id = c.customer_id WHERE c.customer_id IS NULL",
        "Complaints with missing customers": "SELECT COUNT(*) FROM complaints p LEFT JOIN customers c ON p.customer_id = c.customer_id WHERE c.customer_id IS NULL",
        "Complaints with missing accounts": "SELECT COUNT(*) FROM complaints p LEFT JOIN accounts a ON p.account_id = a.account_id WHERE p.account_id IS NOT NULL AND a.account_id IS NULL",
        "Complaints with wrong account owners": "SELECT COUNT(*) FROM complaints p JOIN accounts a ON p.account_id = a.account_id WHERE p.customer_id <> a.customer_id",
        "Requests with missing customers": "SELECT COUNT(*) FROM service_requests r LEFT JOIN customers c ON r.customer_id = c.customer_id WHERE r.customer_id IS NOT NULL AND c.customer_id IS NULL",
        "Requests with missing complaints": "SELECT COUNT(*) FROM service_requests r LEFT JOIN complaints p ON r.complaint_id = p.complaint_id WHERE r.complaint_id IS NOT NULL AND p.complaint_id IS NULL",
        "Requests with mismatched customers": "SELECT COUNT(*) FROM service_requests r JOIN complaints p ON r.complaint_id = p.complaint_id WHERE r.customer_id IS NOT NULL AND r.customer_id <> p.customer_id",
    }
    lines.append("")
    for label, sql in checks.items():
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        lines.append(f"{label}: {count}")
        if count:
            raise SeedError("Integrity check failed: " + label)
    return lines


def run(args):
    folder = Path(args.data_dir).resolve()
    log_path = folder / "seed_run_log.txt"
    report_path = folder / "integrity_report.txt"
    rejection_path = folder / "rejected_rows.csv"
    log = []

    def record(message):
        log.append(message)
        print(message)

    try:
        record("1. Checking CSV files")
        data, problems = load_csvs(folder)
        with rejection_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["file", "row", "reason"])
            writer.writerows(problems)
        if problems:
            record(f"Validation failed: {len(problems)} problem(s). See rejected_rows.csv.")
            raise SeedError("Input validation failed. Database was not changed.")
        for table in TABLES:
            record(f"   {table}: {len(data[table])} rows checked")

        schema = schema_statements(folder / "starter_database.sql", args.backend)
        record("2. Connecting to database")
        db = connect(args.backend, Path(args.db).resolve())
        try:
            cursor = db.cursor()
            try:
                if args.backend == "sqlite":
                    cursor.execute("BEGIN")

                if args.reset:
                    record("3. Reset requested. Dropping old tables")
                    for table in ["service_requests", "complaint_status_history", "complaints", "accounts", "customers"]:
                        cursor.execute("DROP TABLE IF EXISTS " + table)
                else:
                    record("3. Creating tables (no reset)")

                for statement in schema:
                    cursor.execute(statement)

                record("4. Loading rows")
                for table, columns in COLUMNS.items():
                    placeholders = ", ".join(["%s"] * len(columns))
                    sql = "INSERT INTO " + table + " (" + ", ".join(columns) + ") VALUES (" + placeholders + ")"
                    for row in data[table]:
                        values = [row[col] if row[col] != "" else None for col in columns]
                        query(cursor, sql, values, args.backend)
                    record(f"   {table}: {len(data[table])} inserted")

                record("5. Checking counts and foreign keys")
                report_lines = check_integrity(cursor, {table: len(rows) for table, rows in data.items()})
                db.commit()
            except Exception:
                db.rollback()
                record("Database transaction rolled back.")
                raise
            finally:
                cursor.close()
        finally:
            db.close()

        report_path.write_text("INTEGRITY REPORT\n\n" + "\n".join(report_lines) +
                               "\n\nResult: PASS\n", encoding="utf-8")
        record("6. Done. Integrity checks passed.")
        return 0
    except (SeedError, OSError, sqlite3.Error) as error:
        # No passwords or raw connection strings in errors.
        record("ERROR: " + str(error))
        return 1
    except Exception as error:
        record("ERROR: Database operation failed (" + type(error).__name__ + ").")
        return 1
    finally:
        try:
            log_path.write_text("\n".join(log) + "\n", encoding="utf-8")
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Create and seed the complaint training database")
    parser.add_argument("--backend", choices=["sqlite", "postgres"], default="sqlite")
    parser.add_argument("--db", default=str(HERE / "complaints_training.db"), help="SQLite file location")
    parser.add_argument("--data-dir", default=str(HERE), help="Folder with SQL and CSV files")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate existing tables")
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
