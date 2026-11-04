# Exercise 3.2.2: Implementation notes

## What I added

- Three GET endpoints to read customers, complaints, and a customer's complaints.
- POST `/complaints` to create a complaint, returning `201` and a `Location` header.
- PATCH `/complaints/{id}/status` to validate and update the status.
- Pydantic schemas for request validation and clear responses.
- Error handling for missing records (404), invalid bodies (422), and blocked changes (409).
- Automated API tests and OpenAPI evidence.

## How the code works

1. The **router** receives the HTTP request and Pydantic checks its fields.
2. `ComplaintService` checks business conditions and status rules.
3. **SQLAlchemy repositories** read or save the records.
4. The **database** stores the current complaint and its status history.

There is no SQL in the routers or service.

## Important choices

- A customer with zero complaints returns `[]`; an unknown customer returns 404.
- A new complaint starts with `OPEN` and gets an opening history event.
- An allowed status change also records a history event.
- The status and history are saved together by the SQLAlchemy repository.
- The original database has no `ESCALATED` complaint status. Escalation is a separate review decision, so PATCH with `ESCALATED` returns 409.
- Tests inject a service that uses an isolated SQLite database through SQLAlchemy. Production configuration targets PostgreSQL.
- A missing or unavailable PostgreSQL database returns 503 without exposing credentials.

## Things this exercise does not add

- User authentication, permissions, or public deployment.
- New approval policies, transaction features from 3.3.1, or later Sprint 3 exercises.
- A database migration for existing PostgreSQL tables.

For the required request and response examples, see `API_3_2_2_EVIDENCE.md`.
