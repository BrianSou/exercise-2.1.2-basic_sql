# Banking Complaint API

FastAPI + SQLAlchemy. Exercise 3.2.2 adds customer and complaint routes to the health checks from 3.2.1.

## Setup (Linux)

From the project folder:

```bash
python -m pip install -r requirements-dev.txt
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=complaints_training
export DB_USER=training_user
read -rsp "Database password: " DB_PASSWORD; echo
export DB_PASSWORD
```

PostgreSQL must be running and the database/user must already exist. The API uses the **original singular table names** (`customer`, `account`, `complaint`, `complaint_status_history`), not the separate bulk dataset's plural names.

For a new, empty training database only, you can add the original Week 2 sample records:

```bash
python -m src.api.seed_demo --seed
```

This command creates the four needed tables and imports 10 customers, 10 accounts, 30 complaints and 30 status events. It refuses to overwrite populated tables. It is optional and is not run when the API starts. Do not use it in a production database.

Start the server:

```bash
python -m uvicorn src.api.main:app --reload
```

Open `/docs` in your local browser for the interactive API and `/openapi.json` for the schema.

## Routes

| Method | Route | Result |
|---|---|---|
| GET | `/customers/{id}` | Customer, or 404 |
| GET | `/complaints/{id}` | Complaint, or 404 |
| GET | `/customers/{id}/complaints` | List of complaints, or 404 if customer is missing |
| POST | `/complaints` | Create complaint, return 201 and the new complaint ID |
| PATCH | `/complaints/{id}/status` | Validate status change and save a history event |
| GET | `/health/live` | 200 if API is running |
| GET | `/health/ready` | 200 if PostgreSQL responds, otherwise 503 |

### Create a complaint

In `/docs`, use POST `/complaints` with:

```json
{
  "complaint_id": "CMP999",
  "customer_id": "CUS001",
  "account_id": "ACC001",
  "category": "Fee Dispute",
  "priority": "High",
  "created_by": "EMP001",
  "complaint_text": "Unexpected fee"
}
```

On success: `201 Created`, the returned object has `complaint_id: "CMP999"` and `status: "OPEN"`. A `Location` header points to `/complaints/CMP999`.

### Update the status

Use PATCH `/complaints/CMP999/status` with:

```json
{
  "status": "IN_PROGRESS",
  "changed_by": "EMP001",
  "comments": "Investigation started"
}
```

On success: `200 OK`. Both the complaint's status and its status-history event are saved together.

### Error codes

- **404:** customer or complaint does not exist.
- **422:** invalid request fields or an account not owned by that customer.
- **409:** duplicate complaint ID, blocked status transition or database constraint conflict.
- **503:** database is unavailable or missing required tables.

The original Week 2 schema stores escalation decisions separately. Therefore, this API returns 409 if asked to change `complaint.status` to `ESCALATED`.

## Transactions (Exercise 3.3.1)

Creating a complaint inserts both the complaint and its opening status event in one SQLAlchemy transaction. If either insert fails, both are rolled back. See `docs/transaction_evidence.md` for the forced-failure test and database results.

## Tests

```bash
python -m pytest tests/test_api_contract.py tests/test_api_health.py -q
python -m pytest tests -q
```

The tests use a separate temporary SQLite database through SQLAlchemy. They do not modify PostgreSQL.

For recorded normal and error responses, see `docs/API_3_2_2_EVIDENCE.md` and `docs/openapi_3_2_2.json`.

## Architecture

- `src/api/routers/`: HTTP input and output, no SQL.
- `src/api/schemas.py`: Pydantic request and response validation.
- `src/api/dependencies.py`: builds a service for the API using SQLAlchemy.
- `src/services/complaint_service.py`: customer/account checks and status rules.
- `src/domain/models.py`: allowed categories, priorities and status transitions.
- `src/data/`: SQLAlchemy ORM, repositories, sessions and database writes.

**Limitations:** This training API has no authentication or authorization yet. Do not expose it on a public network or use real customer data. The optional PostgreSQL demo setup only creates the four tables needed for these routes. The accepted status transition rules remain training assumptions, not approved bank policy.

## Structured errors and logs (Exercise 3.3.2)

All API errors now return the same three fields: `code`, `message` and `correlation_id`.

```json
{"code":"CUSTOMER_NOT_FOUND","message":"Customer not found","correlation_id":"example-123"}
```

The response includes an `X-Correlation-ID` header. JSON logs have the same ID, plus the HTTP route template, status, outcome and elapsed time. Complaint text, passwords, customer records and stack traces are not logged.

Known codes: `CUSTOMER_NOT_FOUND` (404), `COMPLAINT_NOT_FOUND` (404), `INVALID_STATUS_TRANSITION` (409), `VALIDATION_ERROR` (422), `DEPENDENCY_UNAVAILABLE` (503), and `INTERNAL_ERROR` (500). Duplicate IDs and other constraint conflicts use `CONFLICT` (409). Old exercise files that show a `detail` JSON body are historical evidence from before this change.

## Local `.env` configuration

Instead of exporting credentials every time, copy `.env.example` to `.env` and edit the placeholder values. `python-dotenv` loads the file automatically, but real environment variables take priority. `.env` is excluded from Git.

```bash
cp .env.example .env
python -m pip install -r requirements-dev.txt
python -m uvicorn src.api.main:app --reload
```

Restart Uvicorn after editing database settings because the SQLAlchemy engine is cached.

## New tests

```bash
python -m pytest tests/unit -q
python -m pytest tests/integration -q
REVERSE_TEST_ORDER=1 python -m pytest tests/integration -q
```

These tests use temporary SQLAlchemy SQLite databases. They do not require a live PostgreSQL server. See `docs/exercise_3_3_2/`, `docs/exercise_3_4_1/`, `docs/exercise_3_4_2/` and `docs/exercise_3_5_1/`.
