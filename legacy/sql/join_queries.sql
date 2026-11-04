-- 1. Show each complaint with the customer's name.
SELECT c.complaint_id,
       u.first_name || ' ' || u.last_name AS customer_name,
       c.category, c.status
FROM complaint AS c
JOIN customer AS u ON u.customer_id = c.customer_id
ORDER BY c.complaint_id;

-- 2. Include account type, but keep complaints with no account.
SELECT c.complaint_id,
       u.first_name || ' ' || u.last_name AS customer_name,
       a.account_type
FROM complaint AS c
JOIN customer AS u ON u.customer_id = c.customer_id
LEFT JOIN account AS a ON a.account_id = c.account_id
ORDER BY c.complaint_id;

-- 3. Compare the original and joined complaint counts.
SELECT (SELECT COUNT(*) FROM complaint) AS before_join,
       COUNT(*) AS after_join,
       COUNT(DISTINCT c.complaint_id) AS distinct_complaints
FROM complaint AS c
JOIN customer AS u ON u.customer_id = c.customer_id
LEFT JOIN account AS a ON a.account_id = c.account_id;

-- 4. Check that complaints without accounts are still in the view.
SELECT complaint_id, customer_id, account_id
FROM complaint_analyst_view
WHERE account_id IS NULL
ORDER BY complaint_id;
