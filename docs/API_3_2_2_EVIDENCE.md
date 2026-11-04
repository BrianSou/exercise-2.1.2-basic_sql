> Historical snapshot from Exercise 3.2.2. Current errors use `code`, `message` and `correlation_id` as implemented in Exercise 3.3.2. See `docs/exercise_3_3_2/failure_matrix.csv`.

# Exercise 3.2.2: API test evidence

These responses were captured by sending real HTTP requests through FastAPI TestClient to a temporary SQLAlchemy SQLite database seeded from the original 30-complaint dataset. They are not claims about a live PostgreSQL server.

| Scenario | Request | Status | What happened |
|---|---|---|---|
| Read customer | `GET /customers/CUS001` | 200 | Returned CUS001 and its name |
| Read complaint | `GET /complaints/CMP001` | 200 | Returned CMP001 |
| List complaints | `GET /customers/CUS001/complaints` | 200 | Returned 4 complaint(s) for CUS001 |
| Missing customer | `GET /customers/CUS404` | 404 | Customer not found |
| Missing complaint | `GET /complaints/CMP404` | 404 | Complaint not found |
| Create complaint | `POST /complaints` | 201 | Created CMP999 with status OPEN and Location header |
| Duplicate complaint | `POST /complaints` | 409 | Complaint ID already exists |
| Invalid request | `POST /complaints` | 422 | Pydantic rejected unsupported priority |
| Forbidden transition | `PATCH /complaints/CMP999/status` | 409 | OPEN to CLOSED blocked |
| Valid transition | `PATCH /complaints/CMP999/status` | 200 | OPEN to IN_PROGRESS; history saved |
| Missing status target | `PATCH /complaints/CMP404/status` | 404 | Complaint not found |
| Invalid status value | `PATCH /complaints/CMP999/status` | 422 | Pydantic rejected unsupported status |

## Example bodies

**POST /complaints**

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

**PATCH /complaints/CMP999/status**

```json
{
  "status": "IN_PROGRESS",
  "changed_by": "EMP001",
  "comments": "Started review"
}
```

## Selected captured responses

### Read customer (200)

```json
{
  "customer_id": "CUS001",
  "first_name": "William",
  "last_name": "Johnson",
  "email": "william@email.com"
}
```

### Missing customer (404)

```json
{
  "detail": "Customer not found"
}
```

### Create complaint (201)

```json
{
  "complaint_id": "CMP999",
  "customer_id": "CUS001",
  "account_id": "ACC001",
  "category": "Fee Dispute",
  "status": "OPEN"
}
```

Location header: `/complaints/CMP999`

### Duplicate complaint (409)

```json
{
  "detail": "Complaint ID already exists"
}
```

### Forbidden transition (409)

```json
{
  "detail": "Cannot change status from OPEN to CLOSED"
}
```

### Valid transition (200)

```json
{
  "complaint_id": "CMP999",
  "customer_id": "CUS001",
  "account_id": "ACC001",
  "category": "Fee Dispute",
  "status": "IN_PROGRESS"
}
```

## Database verification

- Complaint CMP999 has 2 history events after creation and an allowed update.
- Stored status changes: [(None, 'OPEN'), ('OPEN', 'IN_PROGRESS')].
- The blocked OPEN to CLOSED attempt did not create a history event.
- A new complaint starts as OPEN.

## OpenAPI

- Contract snapshot: `docs/openapi_3_2_2.json`.
- `/docs` and `/openapi.json` return 200 in the tests.

## Test command

```bash
python -m pytest tests/test_api_contract.py tests/test_api_health.py -q
```

## Limits

- These tests use a temporary SQLite database with SQLAlchemy, not live PostgreSQL.
- The PostgreSQL schema must contain the original singular tables.
- The app has no authentication or role-based authorization. Keep it on localhost with synthetic data.
- Status transitions are documented training rules, not an approved bank policy.
