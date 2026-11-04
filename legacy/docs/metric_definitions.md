# Metric definitions

- **Volume by status:** Count complaints in each current status. This is not status history.
- **Volume by category:** Count complaints in each current category.
- **Volume by month:** Count by the month in `received_at`, not closure month.
- **Open backlog:** Complaints with status other than `CLOSED`.
- **Escalated backlog:** Unresolved complaints with an `ESCALATED` reviewer decision. A historical escalation might no longer be active.
- **Distinct customers:** Number of different customer IDs that have complaints.
- **Average resolution days:** Not available from the original `complaint.csv`, which has no reliable closure date. Do not use `service_request.closed_at` as a substitute. The separate 120-row dataset has `date_closed` and can calculate this metric.
