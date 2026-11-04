# Exercise 3.1.2: Service layer notes

## Before

The Week 2 repository used direct `sqlite3` calls. It worked but was tied to SQLite and mixed database connection handling with raw SQL calls.

## After

- `ComplaintService` handles complaint creation and status changes.
- The domain models check categories, priorities and status transitions.
- SQLAlchemy ORM mappings are in `src/data/orm_models.py`.
- Repositories use SQLAlchemy Sessions to read and write records.
- `DatabaseManager` starts a Session, commits on success, and rolls back on error.
- The service receives repositories in its constructor, so tests can pass fake repositories.

## Why it is separated

- Domain: what data and status changes are valid.
- Service: what steps an operation needs.
- Repository: how records are saved.
- Database manager: connection and transaction lifecycle.
- Router: HTTP behavior only (added later).

Creating a complaint also creates its first status event. Updating a status also creates an event. Each pair is saved in one transaction. If either write fails, both changes roll back.

## Checks and limits

Tests cover creation, invalid inputs, account ownership, allowed and blocked transitions, dependency replacement, and rollback after a failed history insert. Tests use fake repositories and isolated SQLAlchemy databases.

The original schema has no `ESCALATED` value in `complaint.status`, so a separate review decision would be needed for a real escalation. A complete escalation workflow is outside this exercise.
