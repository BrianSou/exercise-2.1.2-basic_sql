# Advanced SQL notes

- `CASE` groups unresolved complaints by 0-7, 8-30, and 31+ days.
- CTEs break repeat-customer and escalation logic into named steps.
- `ROW_NUMBER()` finds the latest status using timestamp and history ID.
- `PARTITION BY complaint_id` restarts numbering for each complaint.
- `RANK()` gives tied complaint counts the same rank.
- `LEFT JOIN` keeps cases with no history record.
- Aging results depend on the date the query runs.
