# Exercise 3.2.2: Tests

Ran from the repository root:

```bash
python -m pytest tests -q
python -m pytest bulk/tests -q
```

Results:

- Main repository: **132 passed**.
- Bulk database tests: **13 passed**.
- Total: **145 passed**.
- New API contract tests: **31 passed**, included in the 132.
- Optional PostgreSQL demo loader: **1 passed**, included in the 132.

The API tests use FastAPI TestClient against a temporary SQLite database through SQLAlchemy. The live PostgreSQL connection was not tested because credentials and a running server are not available in this environment.

The request/response evidence and OpenAPI snapshot were generated from the running FastAPI test application.
