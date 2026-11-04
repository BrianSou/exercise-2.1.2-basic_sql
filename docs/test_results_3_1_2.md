# Exercise 3.1.2: Test results

Tested on October 29, 2026.

- Complaint service tests: 24 passed.
- Domain and service tests together: 54 passed.
- Full suite, including earlier exercises: 87 passed.
- Running `python -m src.services.demo` created and advanced a complaint in a temporary database.
- The demo did not modify the saved training database.

The tests include missing customers, account ownership, duplicate complaints, invalid category and priority values, allowed and blocked status changes, fake repositories, and transaction rollback.

Run the tests yourself:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/ bulk/tests/
```

The service uses SQLite. The API routes and authentication have not been implemented yet.
