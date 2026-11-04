-- 1. All open complaints.
SELECT complaint_id, customer_id, category, status, received_at
FROM complaint WHERE status = 'OPEN';

-- 2. High-priority complaints that are not closed.
SELECT complaint_id, priority, status FROM complaint
WHERE priority = 'High' AND status <> 'CLOSED';

-- 3. Complaint count by status.
SELECT status, COUNT(*) AS complaint_count FROM complaint GROUP BY status;

-- 4. Complaint count by category.
SELECT category, COUNT(*) AS complaint_count FROM complaint GROUP BY category;

-- 5. Complaints for one customer. Replace CUS001 when needed.
SELECT complaint_id, customer_id, category, status FROM complaint
WHERE customer_id = 'CUS001';

-- 6. Half-open date range includes all hours on January 3 through 9.
SELECT complaint_id, received_at, category FROM complaint
WHERE received_at >= '2025-01-03' AND received_at < '2025-01-10';

-- 7. Check closed complaints without a recorded CLOSED status-history event.
-- This is only a history check, not a closure-date check: complaint has no closed_at.
SELECT c.complaint_id, c.status FROM complaint AS c
WHERE c.status = 'CLOSED' AND NOT EXISTS (
  SELECT 1 FROM complaint_status_history AS h
  WHERE h.complaint_id = c.complaint_id AND h.new_status = 'CLOSED'
);

-- 8. Ten newest complaints.
SELECT complaint_id, category, status, received_at FROM complaint
ORDER BY received_at DESC, complaint_id DESC LIMIT 10;
