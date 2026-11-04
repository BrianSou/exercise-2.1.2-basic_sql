# Untested risks

- The transition table is a training assumption. The bank's approved workflow has not been provided.
- Unit tests use fake repositories. Database constraints and actual SQL are covered in integration tests instead.
- There is no authentication or authorization for the API yet.
- Live PostgreSQL behavior, including concurrency and permissions, has not been checked here.
- Long-term API performance and high request volume have not been measured.
- Idempotent response replay is not implemented. Duplicate IDs are rejected with 409.

These limits should be reviewed before treating the project as production-ready.
