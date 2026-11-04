# Exercise 3.3.1: Add Transactional Persistence

## What changed

Creating a complaint saves two records together:

1. A row in `complaint`.
2. An opening `OPEN` event in `complaint_status_history`.

SQLAlchemy uses one session for both writes. `flush()` sends each insert; `commit()` runs only when both succeed. If the history insert fails, `rollback()` undoes the complaint insert too.

## Files

- `src/data/complaint_repository.py`: The two inserts in one transaction.
- `src/data/database_manager.py`: Commits on success and rolls back on failure (existing component).
- `src/services/complaint_service.py`: Creates the complaint and opening event (existing component).
- `tests/test_transactions.py`: Success, rollback, repeated request, and safe error tests.
- `docs/transaction_evidence.md`: Results, database checks, and idempotency notes.

## Run tests

From the project folder, with your virtual environment active:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_transactions.py -v
python -m pytest tests -q
```

Tests create temporary SQLite databases using SQLAlchemy. No PostgreSQL setup is needed to run them.

## Important point

`flush()` is **not** the same as `commit()`. It sends data to the database inside the current transaction. The data only becomes permanent when the transaction commits.

Submitting the same complaint ID again returns `409`, so no duplicate row is created. Full retry idempotency with a separate idempotency key is not implemented.
