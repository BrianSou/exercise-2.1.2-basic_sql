# Verified test results

Tests were run against the updated repository after implementing Exercises 3.3.2 through 3.5.1.

| Command | Result |
|---|---|
| `python -m pytest tests/unit -v --disable-warnings` | 30 passed |
| `python -m pytest tests/integration -v --disable-warnings` | 12 passed |
| `REVERSE_TEST_ORDER=1 python -m pytest tests/integration -v --disable-warnings` | 12 passed |
| `python -m pytest tests -q --disable-warnings` | 182 passed |
| `python -m pytest bulk/tests -q --disable-warnings` | 13 passed |
| `python -m scripts.capture_error_evidence` | 7 error scenarios, 8 sanitized log entries generated |

The 182 main tests already include the new 30 unit and 12 integration tests. Do not add them again when reporting the total.

There are **195 unique passing tests** across the main and bulk suites. The second integration run verifies repeatability and reversed order, not 12 additional unique tests.

The tests use SQLite through SQLAlchemy; a live PostgreSQL server has not been validated here. The exercise 3.5.1 merge gate remains pending human approval.
