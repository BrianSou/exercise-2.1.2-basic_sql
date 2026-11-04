-- One row per complaint. Keep personal details out of the reusable view.
DROP VIEW IF EXISTS complaint_analyst_view;
CREATE VIEW complaint_analyst_view AS
SELECT c.complaint_id, c.customer_id, c.account_id,
       c.category, c.priority, c.status, c.received_at, c.channel,
       a.account_type, a.status AS account_status,
       u.segment AS customer_segment
FROM complaint AS c
JOIN customer AS u ON u.customer_id = c.customer_id
LEFT JOIN account AS a ON a.account_id = c.account_id;
