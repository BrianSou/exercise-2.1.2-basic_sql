# Transaction Scenarios

1. Complaint and initial status event both succeed.
2. Status event insert fails after complaint insert: rollback must leave neither.
3. Repeated request: document idempotency approach.
