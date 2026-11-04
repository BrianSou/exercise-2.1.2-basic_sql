# Pull request summaries

## Exercise 3.1.1

Created typed Customer, Account, Complaint and ComplaintStatusEvent models with controlled category, priority and status values. Added transition rules and tests. Kept domain models separate from SQLAlchemy mappings so business rules do not depend on the database.

## Exercise 3.1.2

Refactored the complaint service to use SQLAlchemy repositories and sessions. The service validates creation and status changes, while the repositories handle queries and writes. Added fake-repository tests and rollback tests for complaint history.

## Exercise 3.2.1

Created the FastAPI foundation, PostgreSQL configuration and health endpoints. Readiness uses a SQLAlchemy engine and a simple SELECT 1 check. Added API tests for working and unavailable databases, safe errors and OpenAPI documentation.

## Exercise 3.2.2

Added customer and complaint REST endpoints using FastAPI, Pydantic, and the existing SQLAlchemy service/repositories. Implemented GET, POST, and PATCH requests with appropriate response codes and recorded complaint status history. Added tests for successful requests, missing records, invalid inputs, and blocked status changes. The local test suite passed using an isolated database; live PostgreSQL still needs verification.

## Exercise 3.3.1

Made the complaint and initial history inserts an explicit SQLAlchemy transaction. Both writes commit together or roll back together. Added tests that force the second insert to fail and verify no partial complaint remains. Documented safe error responses and how duplicate requests are handled.
