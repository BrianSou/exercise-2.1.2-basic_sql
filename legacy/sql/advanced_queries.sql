-- ADVANCED SQL QUESTIONS - Banking Complaint Analysis
-- SQLite | data: October 22, 2026 CSV exports
-- Dates: date('now') uses the UTC calendar day in SQLite.
-- Run each complete statement from WITH through semicolon.



-- Step 1: Unresolved complaint counts by age bucket
-- A CTE gives each unresolved complaint an age in whole calendar days.
WITH unresolved_ages AS (
    SELECT
        complaint_id,
        CAST(julianday(date('now')) - julianday(date(received_at)) AS INTEGER) AS age_days
    FROM complaint
    WHERE status <> 'CLOSED'
      AND received_at IS NOT NULL
      AND date(received_at) <= date('now')
),
bucketed_complaints AS (
    SELECT
        complaint_id,
        CASE
            WHEN age_days BETWEEN 0 AND 7 THEN '0-7 days'
            WHEN age_days BETWEEN 8 AND 30 THEN '8-30 days'
            ELSE '31+ days'
        END AS age_bucket
    FROM unresolved_ages
),
all_buckets AS (
    SELECT 1 AS bucket_order, '0-7 days' AS age_bucket
    UNION ALL SELECT 2, '8-30 days'
    UNION ALL SELECT 3, '31+ days'
)
SELECT
    a.age_bucket,
    COUNT(b.complaint_id) AS complaint_count
FROM all_buckets a
LEFT JOIN bucketed_complaints b ON a.age_bucket = b.age_bucket
GROUP BY a.bucket_order, a.age_bucket
ORDER BY a.bucket_order;


-- Step 1 boundary test: create dates exactly 7, 8, 30, 31 days ago.
WITH boundary_dates AS (
    SELECT 7 AS age_days, date('now', '-7 days') AS received_date
    UNION ALL SELECT 8, date('now', '-8 days')
    UNION ALL SELECT 30, date('now', '-30 days')
    UNION ALL SELECT 31, date('now', '-31 days')
)
SELECT
    received_date,
    CAST(julianday(date('now')) - julianday(received_date) AS INTEGER) AS age_days,
    CASE
        WHEN julianday(date('now')) - julianday(received_date) BETWEEN 0 AND 7 THEN '0-7 days'
        WHEN julianday(date('now')) - julianday(received_date) BETWEEN 8 AND 30 THEN '8-30 days'
        ELSE '31+ days'
    END AS age_bucket
FROM boundary_dates
ORDER BY age_days;


-- Step 2: Repeat customers and their complaints' escalation decisions.
-- Each CTE is named for the business fact it represents.
WITH repeat_complainants AS (
    SELECT customer_id, COUNT(*) AS complaint_count
    FROM complaint
    GROUP BY customer_id
    HAVING COUNT(*) > 1
),
escalation_context AS (
    SELECT DISTINCT rr.complaint_id
    FROM review_request rr
    JOIN review_decision rd
        ON rr.review_request_id = rd.review_request_id
    WHERE rd.decision = 'ESCALATED'
)
SELECT
    c.customer_id,
    c.complaint_id,
    c.category,
    c.status,
    r.complaint_count,
    CASE WHEN e.complaint_id IS NULL THEN 0 ELSE 1 END AS was_escalated
FROM complaint c
JOIN repeat_complainants r ON c.customer_id = r.customer_id
LEFT JOIN escalation_context e ON c.complaint_id = e.complaint_id
ORDER BY c.customer_id, c.complaint_id;


-- Step 3a: The latest recorded status-history entry for each complaint.
WITH numbered_statuses AS (
    SELECT
        complaint_id,
        new_status,
        changed_at,
        history_id,
        ROW_NUMBER() OVER (
            PARTITION BY complaint_id
            ORDER BY changed_at DESC, history_id DESC
        ) AS status_row
    FROM complaint_status_history
)
SELECT
    c.complaint_id,
    c.status AS current_status,
    n.new_status AS latest_history_status,
    n.changed_at AS status_changed_at,
    n.history_id
FROM complaint c
LEFT JOIN numbered_statuses n
    ON c.complaint_id = n.complaint_id AND n.status_row = 1
ORDER BY c.complaint_id;


-- Step 3b: Rank customers by complaint count.
WITH customer_complaint_counts AS (
    SELECT customer_id, COUNT(*) AS complaint_count
    FROM complaint
    GROUP BY customer_id
)
SELECT
    customer_id,
    complaint_count,
    RANK() OVER (ORDER BY complaint_count DESC) AS complaint_rank,
    ROW_NUMBER() OVER (
        ORDER BY complaint_count DESC, customer_id ASC
    ) AS display_order
FROM customer_complaint_counts
ORDER BY display_order;


-- Validation: show actual escalated decisions, including customers who are not repeats.
SELECT DISTINCT rr.complaint_id, rd.decision
FROM review_request rr
JOIN review_decision rd ON rr.review_request_id = rd.review_request_id
WHERE rd.decision = 'ESCALATED'
ORDER BY rr.complaint_id;


-- Validation: compare complaint totals with unresolved and customer totals.
SELECT
    COUNT(*) AS total_complaints,
    SUM(CASE WHEN status <> 'CLOSED' THEN 1 ELSE 0 END) AS unresolved_complaints,
    COUNT(DISTINCT customer_id) AS distinct_customers
FROM complaint;
