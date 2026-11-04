# Review reflection

The most important improvement was making API failures predictable. Before this exercise, different routes returned different error bodies. Now a caller gets an error code, a short message and a correlation ID. The same ID appears in the request log without exposing complaint text.

Unit tests check business rules quickly without a database. Integration tests confirm that FastAPI, the service, SQLAlchemy and the database work together. The rollback test is important because a failed history insert must not leave an unfinished complaint.

I also learned that a passing test suite is not the same as approval to merge. The code still needs a human review and a live PostgreSQL check. The transition rules must be confirmed against the actual bank specification.
