# Exercise requirements check

Checked against the four extra files provided for Week 2.

| Exercise | What the file asks for | Where it is handled |
|---|---|---|
| 2.1.1 | Customer, account, complaint, history, service requests, audit, and a data dictionary | `legacy/sql/database_schema.sql`, `legacy/docs/data_dictionary.md`, `legacy/docs/complaint_erd.png` |
| 2.2.1 | Customer name, optional account type, distinct row counts, complaint-grain view | `legacy/sql/join_queries.sql`, `legacy/sql/complaint_analyst_view.sql` |
| 2.2.2 | Status, category, month, backlog, unique customers, closure time | `legacy/sql/complaint_metrics.sql` and `legacy/docs/metric_definitions.md` |
| 2.3.1 | Age buckets, repeat customers, latest status, customer ranking | `legacy/sql/advanced_queries.sql` |

## Data limits

- The original 30-complaint table has no closure timestamp. Its average resolution days is **not available**. For a working calculation using a *different* dataset, run `bulk/sql/closed_case_resolution.sql` on `data/bulk.db`.
- The original `service_request.csv` has customer and account IDs, but no complaint ID. The question about linking service requests to individual complaints cannot be implemented from this CSV without changing the source contract. The current schema leaves these requests as customer/account-linked records.
- The original source has some status history and audit records. There is no automatic database trigger guaranteeing that every future change creates a history/audit row.
- The five bulk service requests are sample data added in an earlier exercise, not official supplied cases.
- An approved Week 1 release was not supplied. This is a working local training repository, not an approved production implementation.

## Basic definitions

- A complaint is counted once, even when the customer has multiple accounts.
- An unresolved complaint is one whose status is not `CLOSED`.
- Escalation is taken from an `ESCALATED` review decision rather than guessing from `UNDER_REVIEW`.
- Customer ranking counts each complaint; tied counts share rank.
- The age-bucket query uses the date when it runs. Re-running it later can change results.
