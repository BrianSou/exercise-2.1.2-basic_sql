# Complaint Analysis Summary

Analyzed **120 complaints** from `complaints.csv`. 0 rows were skipped.

## Main results

- **Total complaints:** 120
- **Unresolved complaints:** 86 (Open, In Review or Escalated)
- **Distinct customers:** 69
- **Most common category:** Mortgage Servicing (31 complaints, 25.83%)

## Complaints by status

| Status | Count |
|---|---:|
| Closed | 34 |
| Escalated | 30 |
| In Review | 32 |
| Open | 24 |

## Complaints by category

| Category | Count |
|---|---:|
| Mortgage Servicing | 31 |
| Card or Transaction Dispute | 25 |
| Service Quality | 21 |
| Digital Banking | 19 |
| Fees | 15 |
| Account Access | 9 |

## Average resolution days by category

This only uses Closed complaints with valid opened and closed dates.

| Category | Closed cases used | Avg. days |
|---|---:|---:|
| Account Access | 5 | 16.20 |
| Card or Transaction Dispute | 4 | 11.25 |
| Digital Banking | 4 | 8.25 |
| Fees | 6 | 10.33 |
| Mortgage Servicing | 9 | 9.44 |
| Service Quality | 6 | 6.17 |

## Complaints by opened month

| Month | Count |
|---|---:|
| 2026-01 | 14 |
| 2026-02 | 8 |
| 2026-03 | 13 |
| 2026-04 | 13 |
| 2026-05 | 20 |
| 2026-06 | 15 |
| 2026-07 | 15 |
| 2026-08 | 22 |

## Data checks and notes

- 120 source rows were read; 0 incomplete, duplicate or invalid rows were skipped.
- 0 Closed complaints did not have a valid closure date for the average.
- 86 blank date_closed values were found. This is normal for cases that are not closed.
- Missing values were counted for every column in the output CSV.
- `date_opened` is treated as the complaint start date and `date_closed` as the closure date.
- Resolution days = closure date minus start date. Unresolved complaints are excluded from the average.
- Status and category counts reflect this CSV, not historical changes.
- This CSV does not show separate escalation decisions, so it cannot measure the escalation-decision backlog.
- These numbers describe this file only. They do not prove a trend or explain why complaints happened.
