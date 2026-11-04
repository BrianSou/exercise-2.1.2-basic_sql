# Exercise 2.3.2: Hybrid Flow Designs

These examples use the complaint database from the earlier SQL exercises. Each flow uses SQL for the facts, policy documents for the rules, and a short explanation of what should happen next.

## 1. Fee reversal for CMP001

First, check the complaint, fee, and review decision.

```sql
SELECT c.complaint_id, c.status, f.fee_id, f.amount, f.reversed_flag,
       rr.status AS review_status, rd.decision
FROM complaint c
LEFT JOIN fee f ON f.account_id = c.account_id
LEFT JOIN review_request rr ON rr.complaint_id = c.complaint_id
LEFT JOIN review_decision rd ON rd.review_request_id = rr.review_request_id
WHERE c.complaint_id = 'CMP001';
```

1. **SQL result:** The complaint is open. The $35 fee has not been marked as reversed. The decision is `APPROVED`, but the review request still says `PENDING`.
2. **Policy:** Find `POL002 / SEC002` for fee reviews and `POL009 / SEC009` for refund approval. Keep the policy section and version as evidence.
3. **Answer:** The refund may have been approved, but the records do not confirm it was paid. Check the actual reversal record.
4. **Approval:** A manager must confirm the refund and check for an earlier payment before any refund is processed.

If the account has several fees, check the specific fee ID instead of matching only by account.

## 2. Duplicate debit for CMP003

Check the complaint and its transactions.

```sql
SELECT c.complaint_id, c.complaint_text,
       t.transaction_id, t.amount, t.description, rd.decision
FROM complaint c
LEFT JOIN transactions t ON t.account_id = c.account_id
LEFT JOIN review_request rr ON rr.complaint_id = c.complaint_id
LEFT JOIN review_decision rd ON rd.review_request_id = rr.review_request_id
WHERE c.complaint_id = 'CMP003';
```

1. **SQL result:** The customer reported a duplicate debit, but the supplied data shows only one $250 transaction. The review decision is `REQUEST_CHANGES`.
2. **Policy:** Find `POL009 / SEC009` for the refund approval rule. The policy summary does not explain how to prove a duplicate.
3. **Answer:** There is not enough evidence to confirm a duplicate charge. Ask for the missing transaction details.
4. **Approval:** An employee checks both transactions, if they exist, and a manager approves any refund.

Do not treat two transactions with similar amounts as proof they are duplicates.

## 3. Suspected fraud for CMP009

Check the status and review decision.

```sql
SELECT c.complaint_id, c.priority, c.status,
       rr.status AS review_status, rd.decision, rd.decision_reason
FROM complaint c
LEFT JOIN review_request rr ON rr.complaint_id = c.complaint_id
LEFT JOIN review_decision rd ON rd.review_request_id = rr.review_request_id
WHERE c.complaint_id = 'CMP009';
```

1. **SQL result:** The complaint has `Critical` priority, is `UNDER_REVIEW`, and has an `ESCALATED` decision for potential fraud.
2. **Policy:** Find `POL003 / SEC003` for fraud escalation, `POL007 / SEC007` for monitoring, and `POL005 / SEC005` for protecting customer information.
3. **Answer:** The case has already been escalated. Pass the available evidence to the fraud team without claiming fraud has been proven.
4. **Approval:** The fraud team decides whether to restrict or freeze an account. The assistant must not do this on its own.

Being `UNDER_REVIEW` does not automatically mean a complaint was escalated. Check the decision.

## 4. Response deadline for CMP002

Check when the complaint arrived and when a response was sent.

```sql
SELECT c.complaint_id, c.received_at, c.status,
       cr.response_id, cr.sent_date
FROM complaint c
LEFT JOIN customer_response cr ON cr.complaint_id = c.complaint_id
WHERE c.complaint_id = 'CMP002';
```

1. **SQL result:** The complaint arrived on January 5, 2025, and a response is recorded on January 6, 2025.
2. **Policy:** Find `POL004 / SEC004`, which says to respond within two business days.
3. **Answer:** Compare the response date with the deadline. Use a business-day calendar and check whether an earlier response exists before making a final judgment.
4. **Approval:** An employee reviews any overdue notice or customer message before it is sent.

A first response and a fully resolved complaint are two different things.

## 5. Online banking reset for CMP004

Check what was recommended, what the customer was told, and what was logged.

```sql
SELECT c.complaint_id, c.complaint_text,
       r.recommendation_text, cr.response_text,
       a.action_type AS logged_action, a.details AS audit_details
FROM complaint c
LEFT JOIN investigation i ON i.complaint_id = c.complaint_id
LEFT JOIN recommendation r ON r.investigation_id = i.investigation_id
LEFT JOIN customer_response cr ON cr.complaint_id = c.complaint_id
LEFT JOIN audit_log a ON a.entity_name = 'COMPLAINT'
                     AND a.entity_id = c.complaint_id
WHERE c.complaint_id = 'CMP004';
```

1. **SQL result:** The recommendation says to reset the banking profile, and the response says it was done. The available complaint audit log does not prove the reset or identity check took place.
2. **Policy:** Find `POL006 / SEC006` for identity checks, `POL005 / SEC005` for data protection, and `POL010 / SEC010` for audit records.
3. **Answer:** The response claims the reset happened, but there is not enough evidence to confirm the proper checks were followed.
4. **Approval:** An authorized employee checks the identity and account-action logs before confirming the reset or trying it again.

A message saying something was completed is not the same as a system record proving it happened.

## Notes

- The SQL provides the complaint facts. The policy sections provide the rules. The final answer should use both.
- The supplied `policy_section.csv` contains short summaries, not full policy documents. Full documents would be needed for detailed policy decisions.
- These five SQL queries were tested against the supplied CSV data in SQLite.
- This exercise describes the flow only. It does not issue refunds, change accounts, or send messages.
- Exercise 2.4.1 can reuse the SQL and CSV data. Week 4 will use the document retrieval part.
