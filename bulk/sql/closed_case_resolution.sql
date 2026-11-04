-- Run against data/bulk.db, NOT data/original.db.
-- Closed cases only; missing or invalid closure dates are not averaged.
SELECT category,
       COUNT(*) AS closed_complaints,
       ROUND(AVG(julianday(date_closed) - julianday(date_opened)), 2) AS avg_resolution_days
FROM complaints
WHERE UPPER(status) = 'CLOSED'
  AND date_opened IS NOT NULL
  AND date_closed IS NOT NULL
  AND julianday(date_closed) >= julianday(date_opened)
GROUP BY category
ORDER BY category;
