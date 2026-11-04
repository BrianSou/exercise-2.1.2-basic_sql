-- Basic Query Questions
-- Banking Complaint Resolution Assistant

-- ===
-- 1. List all open complaints.
-- ===

SELECT *  
FROM complaint  
WHERE status = 'OPEN';

-- ===
-- 2. List high-priority unresolved complaints.
-- ===

SELECT *
FROM complaint
WHERE priority = 'High' AND status <> 'CLOSED';

-- ===
-- 3. Count complaints by status.
-- ===

SELECT status, COUNT(*) AS complaint_count
FROM complaint
GROUP BY status;

-- ===
-- 4. Count complaints by category.
-- ===

SELECT category, COUNT(*) AS complaint_count
FROM complaint
GROUP BY category;

-- ===
-- 5. Show complaints for a supplied customer ID.
-- ===

SELECT *
FROM complaint
WHERE customer_id = 'CUS001';

-- ===
-- 6. Show complaints opened within a supplied date range.
-- ===

SELECT *
FROM complaint
WHERE received_at BETWEEN '2025-01-03' AND '2025-01-10';

-- ===
-- 7. List closed complaints where date_closed is missing (expected zero).
-- ===

SELECT *
FROM complaint
INNER JOIN service_request
ON complaint.customer_id = service_request.customer_id
WHERE complaint.status = 'CLOSED' AND service_request.closed_at IS NULL;

-- ===
-- 8. Show the ten most recently opened complaints.
-- ===

SELECT *
FROM complaint
ORDER BY received_at DESC
LIMIT 10;
