# Banking Complaint Project

Python, SQLAlchemy and FastAPI exercises for a banking complaint system. Includes SQL queries, database setup, business rules, REST endpoints and tests.

## Get started

Requires Python 3.10+.

```bash
python -m pip install -r requirements-dev.txt
python setup_local.py
python -m pytest tests -q
python -m pytest bulk/tests -q
```

`setup_local.py` creates the local training databases if they are missing.

## Run FastAPI

Copy `.env.example` to `.env`, then enter your own PostgreSQL settings. Do not commit `.env`.

```bash
cp .env.example .env
python -m uvicorn src.api.main:app --reload
```

FastAPI reads `.env` automatically. PostgreSQL must be running for `/health/ready` to return 200.

- `/docs`: interactive API docs
- `/health/live`: checks if the app is running
- `/health/ready`: checks the PostgreSQL connection
- `/customers/{id}`, `/complaints/{id}`: read records
- `POST /complaints`, `PATCH /complaints/{id}/status`: write records

On an **empty training PostgreSQL database only**, you can run `python -m src.api.seed_demo --seed` to create the needed sample tables and records. It refuses to replace populated tables.

## Project folders

| Folder | Purpose |
|---|---|
| `legacy/` | Original SQL exercises and 30-complaint data |
| `bulk/` | Separate 120-complaint dataset and seeder |
| `analysis/` | Python CSV analysis |
| `src/domain/` | Dataclasses and complaint rules |
| `src/data/` | SQLAlchemy models, sessions and repositories |
| `src/services/` | Business operations |
| `src/api/` | FastAPI endpoints, errors and JSON logs |
| `tests/unit/` | Domain and service tests with fake repositories |
| `tests/integration/` | API and SQLAlchemy tests with isolated databases |
| `tests/` | Earlier exercise tests |
| `docs/` | Reports, explanations and review evidence |
| `reference/` | Exercise requirements |
| `data/` | Local SQLite training databases |

`data/original.db` and `data/bulk.db` are different training datasets. The FastAPI app is configured for PostgreSQL with the original singular table names. The old Week 2 setup utilities still use SQLite.

## Verify exercises 3.3.2 through 3.5.1

```bash
python -m pytest tests/unit -q
python -m pytest tests/integration -q
REVERSE_TEST_ORDER=1 python -m pytest tests/integration -q
python -m scripts.capture_error_evidence
```

Start with `README_API.md` for endpoints and `docs/exercise_3_5_1/` for review evidence.

**Limits:** These are training workflows. Authentication and authorization are not implemented. Live PostgreSQL end-to-end testing and coach approval are still needed.
