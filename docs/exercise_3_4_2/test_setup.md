# Exercise 3.4.2: Integration test setup

Integration tests call real FastAPI endpoints through `TestClient` and use SQLAlchemy to check persisted records.

## How test data stays separate

1. `tests/integration/conftest.py` creates a new SQLite database in pytest's `tmp_path` for **every test**.
2. The same Week 2 seed helper adds the initial sample data.
3. FastAPI's `get_complaint_service` dependency is replaced with a service connected to that database.
4. Each test uses real repositories and SQLAlchemy sessions.
5. The test releases the engine after it finishes.

No test writes to the local training databases or PostgreSQL.

## Run both checks

```bash
python -m pytest tests/integration -q
REVERSE_TEST_ORDER=1 python -m pytest tests/integration -q
```

The second run reverses test collection order. Passing both helps show tests do not depend on one another.

## What the tests check

- Customer lookup returns 200 or 404.
- A valid complaint returns 201 and creates a complaint and opening event.
- Invalid input returns 422 without a write.
- A valid status change updates both the complaint and history.
- A blocked transition returns 409 without a write.
- A forced history insert failure rolls back the complaint insert.
- Database unavailability returns 503.
- An unexpected exception returns 500 without private details.
- Correlation IDs appear in both responses and JSON logs.

This is an isolated SQLAlchemy integration test suite, **not a live PostgreSQL test**.
