# Exercise 3.1.2: Complaint service

This exercise adds a business service between the domain models and the repositories.

## Files

- `src/services/complaint_service.py` checks customer, account, creation and status rules.
- `src/services/dependencies.py` constructs the service with the real repositories.
- `src/data/complaint_repository.py` now saves status changes and their history together.
- `tests/test_complaint_service.py` tests the service using fake and real repositories.
- `docs/refactoring_notes.md` explains the before and after design.

## Install and test

Open a terminal from the repository's main folder:

```powershell
python -m pip install pytest
python -m pytest tests/test_complaint_service.py -v
```

Run a small demo without changing your training database:

```powershell
python -m src.services.demo
```

## How to use the service

```python
from src.services.dependencies import build_complaint_service

service = build_complaint_service()

# Read an existing complaint.
complaint = service.get_complaint("CMP001")
print(complaint["status"])

# These operations write to the original database. Use a test database
# if you are experimenting with your own records.
# service.create_complaint("CMP999", "CUS001", "Fee Dispute", "High", "EMP001")
# service.change_status("CMP999", "IN_PROGRESS", "EMP001")
```

`build_complaint_service()` uses `data/original.db`. The methods return plain dictionaries so the later FastAPI routers can easily build responses.

## Why fake repositories?

A fake repository is an in-memory object with the same methods as the real one. It lets us test business rules without setting up a database. The last tests also use a temporary SQLite database to check real inserts, transactions and rollbacks.

## Notes

- New complaints start as `OPEN`.
- Valid transitions come from the existing domain models.
- The `ESCALATED` status is not stored in the original SQLite `complaint` table. It is tracked as a review decision instead.
- The service does not contain SQL or FastAPI routing code. Those responsibilities belong in other layers.
- These are training rules until confirmed against the approved specification.
