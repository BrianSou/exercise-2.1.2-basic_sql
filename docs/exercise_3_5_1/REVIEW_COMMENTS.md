# Self-review comments

These are author review findings. They are not comments from an external reviewer.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R1 | Blocking | API returned inconsistent `detail` responses with no correlation ID. | Added `error_handlers.py` and mapped stable codes. Updated old API tests to assert the new contract. |
| R2 | Blocking | Request failures could reveal exception text if returned directly. | Generic 500 and 503 responses use fixed safe messages. No trace in client responses. |
| R3 | Blocking | No structured request log to connect errors with requests. | Added correlation middleware, safe route-template logging and generated logs from real requests. |
| R4 | Blocking | Previously there was no independent unit/integration suite with the required evidence. | Added `tests/unit`, `tests/integration` and both test reports. |
| R5 | Non-blocking | Request text fields had no explicit maximum. | Added maximum lengths for complaint text and status comments. |
| R6 | Non-blocking | `.env` values required manual terminal exports. | Added `python-dotenv` to API dependencies and `load_dotenv()` to config. `.env` is ignored by Git. |
| R7 | Non-blocking | README did not explain the new error contract or tests. | Updated README_API and added exercise setup notes. |
| R8 | External dependency | PostgreSQL availability and coach approval cannot be verified locally. | Marked as open in risks and merge gate. No approval claimed. |

Blocking **code issues** R1-R4 have been addressed and verified with automated tests. External sign-off is still pending.
