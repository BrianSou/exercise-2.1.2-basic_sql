-- Complaint volumes by status and category.
SELECT status, COUNT(*) AS complaint_count FROM complaint_analyst_view
GROUP BY status ORDER BY complaint_count DESC, status;
SELECT category, COUNT(*) AS complaint_count FROM complaint_analyst_view
GROUP BY category ORDER BY complaint_count DESC, category;

-- The source uses received_at for the receipt month.
SELECT strftime('%Y-%m', received_at) AS received_month,
       COUNT(*) AS complaint_count
FROM complaint_analyst_view GROUP BY received_month ORDER BY received_month;

-- Open backlog includes all non-closed complaints.
SELECT COUNT(*) AS unresolved_count FROM complaint_analyst_view
WHERE status <> 'CLOSED';

-- Reviewer escalation is based on review_decision, not status = UNDER_REVIEW.
SELECT COUNT(DISTINCT rr.complaint_id) AS escalated_unresolved_count
FROM review_request rr JOIN review_decision rd
  ON rd.review_request_id = rr.review_request_id
JOIN complaint c ON c.complaint_id = rr.complaint_id
WHERE rd.decision = 'ESCALATED' AND c.status <> 'CLOSED';

-- Customers affected, counted once each.
SELECT COUNT(DISTINCT customer_id) AS distinct_customers FROM complaint;

-- Closed-case resolution days are NOT computable from original complaint.csv:
-- it does not include a trusted complaint closure date. See metric_definitions.md.
