# Exercise 3.3.2: Errors and logs

## What changed

- `src/api/error_handlers.py` returns a consistent error body.
- `src/api/errors.py` maps service and database exceptions to safe error codes.
- `src/api/main.py` assigns a correlation ID and logs each request.
- `src/api/logging_config.py` writes JSON log lines.
- `scripts/capture_error_evidence.py` records actual failure responses and matching logs.

Error example:

```json
{"code":"CUSTOMER_NOT_FOUND","message":"Customer not found","correlation_id":"example-123"}
```

The response also has an `X-Correlation-ID` header. A caller can supply a short safe ID or the app generates one. Each request gets a log entry with `timestamp`, `level`, `correlation_id`, `operation`, `outcome` and `duration_ms`.

## Mappings

| Problem | HTTP | Code |
|---|---:|---|
| Customer does not exist | 404 | CUSTOMER_NOT_FOUND |
| Complaint does not exist | 404 | COMPLAINT_NOT_FOUND |
| Invalid status change | 409 | INVALID_STATUS_TRANSITION |
| Duplicate ID or constraint conflict | 409 | CONFLICT |
| Invalid fields | 422 | VALIDATION_ERROR |
| Database unavailable | 503 | DEPENDENCY_UNAVAILABLE |
| Unexpected error | 500 | INTERNAL_ERROR |

A missing route uses `NOT_FOUND` (404). These extra codes do not replace the required error catalog.

## Privacy

The logs include route templates, not actual customer IDs or request bodies. They never include database passwords, API keys, complaint text, customer records or exception traces. Unexpected errors return only a safe message.

## Evidence

`failure_matrix.csv` contains seven tested error cases, their response codes and the matching log outcomes. `sample_logs.jsonl` contains eight real sanitized request logs, including one successful POST.

To reproduce both files:

```bash
python -m scripts.capture_error_evidence
```

This uses a temporary SQLite database through SQLAlchemy. It never changes PostgreSQL.
