# Exercise 3.2.1 Test Results

Ran the tests after adding the FastAPI foundation.

- New API tests: 16 passed.
- Full main test suite: 90 passed.
- Bulk database tests: 13 passed.
- Started Uvicorn locally and checked the endpoints.
- `/health/live` returned `200` and `{"status":"ok"}`.
- `/health/ready` returned `503` when PostgreSQL was not configured.
- `/docs` and `/openapi.json` returned `200`.

The ready-success case was tested with a fake PostgreSQL connection. It ran `SELECT 1` and closed the connection. A failed query also closed the connection.

**Limitation:** No live PostgreSQL server was available for this test. The API uses PostgreSQL as required, but successful readiness against a real server still needs to be checked locally.
