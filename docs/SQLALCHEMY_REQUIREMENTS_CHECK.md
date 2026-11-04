# Requirement check: Week 3 exercises 3.1.1 to 3.2.2

The submitted Sprint 3 archive was used to understand the later direction, but **no later exercise was implemented**.

## 3.1.1: Model the Complaint Domain in Python

| Requirement | Evidence |
|---|---|
| Plan four models and rules | `docs/domain_model_notes.md` |
| Typed classes and validation | `src/domain/models.py` |
| SQLAlchemy mappings separate from domain | `src/data/orm_models.py` |
| Valid and invalid model tests | `tests/test_domain_models.py` |
| Controlled values, explicit transitions | `ComplaintCategory`, `ComplaintPriority`, `ComplaintStatus`, `VALID_TRANSITIONS` |
| No SQL or FastAPI in domain models | `src/domain/models.py` only uses standard Python |

## 3.1.2: Create the Complaint Service Layer

| Requirement | Evidence |
|---|---|
| Assess and refactor responsibilities | `docs/refactoring_notes.md` |
| ComplaintService uses repositories | `src/services/complaint_service.py` |
| SQL stays in repositories | `src/data/*_repository.py` and `src/data/orm_models.py` |
| SQLAlchemy sessions and rollback | `src/data/database_manager.py` |
| Replaceable dependencies | `src/services/dependencies.py`; fake repositories in tests |
| Tests for creation/status/error cases | `tests/test_complaint_service.py`, `tests/test_sqlalchemy_integration.py` |

## 3.2.1: Create FastAPI Application and Health Checks

| Requirement | Evidence |
|---|---|
| App, routers, schemas | `src/api/main.py`, `src/api/routers/`, `src/api/schemas.py` |
| External PostgreSQL settings | `src/config.py`, `src/dependencies.py` |
| `/health/live` and `/health/ready` | `src/api/routers/health.py` |
| SQLAlchemy database readiness | `src/dependencies.py` uses `engine.connect()` and `text('SELECT 1')` |
| Installation and run commands | `README_API.md` |
| Available/unavailable readiness tests | `tests/test_api_health.py` |
| OpenAPI documentation | `/docs`, `/openapi.json` tested |
| No credentials exposed | Password hidden in Settings repr, URL masks password, safe 503 response |

## Limitations

- **PostgreSQL requirement:** The API targets PostgreSQL, as the supplied environment guide requires. Readiness is tested with injected and isolated SQLAlchemy connections. No live PostgreSQL server/credentials were provided, so production connectivity is not claimed.
- **Legacy database:** The original Week 2 dataset is SQLite. SQLAlchemy repositories map to its singular tables. The legacy schema was not silently replaced with a different PostgreSQL schema.
- **Status assumptions:** The transition table is documented as a proposal, not approved banking policy. The original database stores escalation in `review_decision` rather than in `complaint.status`.
- **Future scope:** Exercises 3.3.1 and later were not implemented. Exercise 3.2.2 now has all five required REST routes.
- The approved Week 1 specification and a tagged Week 2 release were not uploaded as separate reviewed artifacts; alignment is based on the available Week 2 repository and exercise documents.

## 3.2.2: Build Customer and Complaint REST APIs

| Requirement | Evidence |
|---|---|
| Three GET routes and 404 responses | `src/api/routers/customers.py` and `complaints.py` |
| POST complaint with Pydantic validation and 201 | `src/api/schemas.py`, `src/api/routers/complaints.py` |
| PATCH status and record history | `ComplaintService.change_status()` and SQLAlchemy repository |
| SQL only in repositories | `src/data/*_repository.py` |
| OpenAPI contract | `docs/openapi_3_2_2.json` |
| Positive and negative HTTP examples | `docs/API_3_2_2_EVIDENCE.md` |
| Automated endpoint tests | `tests/test_api_contract.py` |
| Optional isolated PostgreSQL demo seed | `src/api/seed_demo.py` |
