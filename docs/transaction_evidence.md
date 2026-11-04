# Exercise 3.3.1: Transaction Evidence

## 1. Transaction boundary

When the API creates a complaint, it must also save an opening status event.
These two inserts are **one transaction**. They should not be committed separately.

Flow:

1. `POST /complaints` calls `ComplaintService.create_complaint()`.
2. The service checks the customer, account, and complaint fields.
3. `ComplaintRepository.create()` adds the complaint and calls `session.flush()`.
4. The repository adds the opening status event and calls `session.flush()` again.
5. `DatabaseManager.session()` commits when both inserts succeed.
6. If either insert fails, the context manager rolls back and re-raises the error.

`flush()` sends SQL to the database but does **not** commit. The first insert can be undone if the second one fails.

The transaction belongs in the repository/database layer, not the FastAPI router.
The service handles business rules. The repository handles database writes.

Relevant files:

- `src/services/complaint_service.py`
- `src/data/complaint_repository.py`
- `src/data/database_manager.py`
- `src/api/routers/complaints.py`
- `tests/test_transactions.py`

## 2. Verified database results

I used a temporary SQLite database with SQLAlchemy, loaded from the original Week 2 CSVs. The tests do not change the training database or connect to PostgreSQL.

For this check, `CMP999` did not exist before the request. I injected a database error when SQLAlchemy attempted the `complaint_status_history` INSERT, after the complaint INSERT had run.

| Check | Total complaints | Total history events | CMP999 complaints | CMP999 history events |
|---|---:|---:|---:|---:|
| Before request | 30 | 30 | 0 | 0 |
| After forced second-insert failure | 30 | 30 | 0 | 0 |
| After successful retry | 31 | 31 | 1 | 1 |
| After repeating the successful request | 31 | 31 | 1 | 1 |

HTTP responses from that run:

- Failure on second insert: `503` with `{"detail": "Database unavailable"}`.
- Successful request: `201` with status `OPEN`.
- Repeated request: `409` with `{"detail": "Complaint ID already exists"}`.

The API returns a safe message rather than raw SQL errors or connection details.

## 3. How the failure is tested

`test_second_insert_failure_rolls_back_both_and_returns_safe_error` installs a temporary SQLAlchemy event listener on the test engine.

The listener waits for `INSERT INTO complaint_status_history`, then raises an `OperationalError`.
The test confirms:

1. The complaint INSERT was attempted first.
2. The history INSERT failed.
3. The API returned `503` without the internal error text.
4. Neither record was left in the database.
5. Other complaints were still readable.

Other tests check normal creation, an invalid `changed_by` foreign key, repeated requests, retry after rollback, and rollback of a failed status change.

To reproduce:

```bash
python -m pytest tests/test_transactions.py -v
```

To inspect a local SQLite test database manually, these are the queries:

```sql
SELECT COUNT(*) FROM complaint WHERE complaint_id = 'CMP999';
SELECT COUNT(*) FROM complaint_status_history WHERE complaint_id = 'CMP999';
```

After the simulated failure, both should return `0`.

## 4. Repeated requests and idempotency

The current API requires a unique `complaint_id`.
If the same ID is submitted again after a successful create, it returns `409` and does not create another complaint or history event.

This protects against duplicate rows, but it is **not full request idempotency**. For example, if the client loses a successful response and retries, it receives `409` instead of the original `201` result.

A future improvement would be an `Idempotency-Key` header. The server could store the key, request details, and result in the same database transaction, then return the original result for a matching retry. That feature is not implemented in this exercise.

## 5. Limits

- The automated tests run on isolated SQLite databases through SQLAlchemy. Live PostgreSQL transaction behavior has not been tested here.
- The repository's lower-level `create()` method still allows `initial_event=None` for older Week 2 examples. The actual `ComplaintService.create_complaint()` path **always** supplies an opening event.
- Authentication and authorization are not part of this exercise.
