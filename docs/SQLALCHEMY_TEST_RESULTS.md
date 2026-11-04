# SQLAlchemy rebuild test evidence

Executed in the rebuilt repository on 2026-11-02.

| Command | Outcome |
|---|---|
| `python setup_local.py` | Passed, refreshed the original and bulk data |
| `python -m pytest tests -q` | 100 passed |
| `python -m unittest discover -s bulk/tests -q` | 13 passed |
| `python -m src.services.demo` | Created and updated a test complaint in a temporary database |
| `python -m src.demo` | Retrieved a customer, account count, and complaint count |

Tests cover valid and invalid domains, service behavior with fake repositories, SQLAlchemy ORM access, read/write transactions, rollback after event failure, foreign keys, dependency injection, and FastAPI health checks. The isolated SQLite test engine uses SQLAlchemy for SQL and sessions.

The API is configured for PostgreSQL. A live PostgreSQL server was not connected in this environment, so its live readiness-success path was not tested here. The positive readiness case was tested with a real SQLAlchemy connection to an isolated SQLite engine and an injected checker. The unavailable-database response was tested.
