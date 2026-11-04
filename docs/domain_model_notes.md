# Exercise 3.1.1: Domain model notes

## Plan

- `Customer`: identifies the customer.
- `Account`: belongs to a customer.
- `Complaint`: belongs to a customer and may reference an account.
- `ComplaintStatusEvent`: records a status change.

We use Python dataclasses and Enums for domain values. Database table mappings live in `src/data/orm_models.py` and use SQLAlchemy. This keeps SQL and web-framework code out of the domain models, as the exercise requires.

## Controlled values

- Categories: the known values from the original and bulk training datasets.
- Priorities: Low, Medium, High and Critical.
- Statuses: OPEN, IN_PROGRESS, UNDER_REVIEW, ESCALATED and CLOSED.
- The bulk file's "In Review" label maps to UNDER_REVIEW.

## Status changes

| Current | Allowed next |
|---|---|
| OPEN | IN_PROGRESS, UNDER_REVIEW, ESCALATED |
| IN_PROGRESS | UNDER_REVIEW, ESCALATED, CLOSED |
| UNDER_REVIEW | IN_PROGRESS, ESCALATED, CLOSED |
| ESCALATED | IN_PROGRESS, UNDER_REVIEW, CLOSED |
| CLOSED | None |

A new complaint starts as OPEN. The rules above are proposed training rules because the exercise does not supply an approved transition table. **In the original 30-row database, escalation is held in review decisions and ESCALATED is not an allowed value in the complaint table. The service therefore rejects that status in the original database.**

## Choices and limitations

- Domain models are immutable and hold no SQL statements or FastAPI imports.
- SQLAlchemy mappings use the singular Week 2 tables `customer`, `account`, `complaint`, and `complaint_status_history`.
- The existing Week 2 SQLite table stores `received_at` as text. The ORM mapping keeps this compatible with that source and doesn't silently change the database schema.
- Domain objects validate values before the repository writes them.
