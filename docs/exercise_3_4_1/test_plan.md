# Exercise 3.4.1: Unit test plan

| Group | Cases | Expected behavior |
|---|---|---|
| Happy paths | Allowed transitions, valid models, owned account, valid status update | Accept the action and return the expected result |
| Boundaries | New complaint starts OPEN, status cannot stay unchanged, closed cannot reopen | Enforce the exact transition rules |
| Invalid inputs | Empty IDs, missing names, invalid category or priority, invalid date | Raise a clear `ValueError` |
| Missing data | Unknown customer or account | Reject without saving any complaint |
| Escalation | Domain enum vs. original database review decision | `In Review` is not escalation; service blocks setting ESCALATED as complaint status |
| History | Actor and timestamp recorded, invalid transition rejected | Valid event only |

Fixtures in `tests/unit/conftest.py` supply a fixed timestamp and fake customer, account and complaint repositories. The unit tests never use SQLAlchemy or a database. `pytest.mark.parametrize` covers combinations without copying the same test code.

Run:

```bash
python -m pytest tests/unit -v
```
