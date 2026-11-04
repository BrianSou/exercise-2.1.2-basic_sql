# Data dictionary

Source: original banking complaint CSV files. Database: `data/original.db` (SQLite).
One row in `complaint` represents one complaint. Missing optional CSV values are NULL.

## Modeling notes

- Each complaint needs a customer. An account is optional.
- One customer can have multiple accounts and complaints.
- A complaint can have multiple status-history entries.
- Category and priority are stored as text. There are no separate lookup tables.
- Status-history and audit-log rows are imported data. The database does not automatically write a new audit row for every change.
- The supplied `service_request.csv` has no `complaint_id`. Requests can be linked to customers and accounts, but not directly to a complaint in this schema.
- The original complaint table does not have a closure date.

## customer

People who submit complaints and hold accounts.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `customer_id` | Customer identifier | TEXT | Yes | PK | `customer.csv` | CUS001 |
| `first_name` | First name | TEXT | Yes |  | `customer.csv` | William |
| `last_name` | Last name | TEXT | Yes |  | `customer.csv` | Johnson |
| `email` | Email address | TEXT | No |  | `customer.csv` | william@email.com |
| `phone_number` | Phone number | TEXT | No |  | `customer.csv` | 4165551001 |
| `segment` | Customer segment | TEXT | No |  | `customer.csv` | Retail |
| `date_created` | Record creation date | TEXT | No |  | `customer.csv` | 2026-10-20 19:32:47 |

## employee

Bank employees handling complaints and reviews.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `employee_id` | Employee id | TEXT | Yes | PK | `employee.csv` | EMP001 |
| `first_name` | First name | TEXT | Yes |  | `employee.csv` | John |
| `last_name` | Last name | TEXT | Yes |  | `employee.csv` | Smith |
| `email` | Email address | TEXT | No |  | `employee.csv` | john.smith@bank.com |
| `role` | Employee role | TEXT | No |  | `employee.csv` | Analyst |

## account

Accounts owned by customers.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `account_id` | Account identifier | TEXT | Yes | PK | `account.csv` | ACC001 |
| `customer_id` | Customer identifier | TEXT | Yes | FK to customer.customer_id | `account.csv` | CUS001 |
| `account_number` | Account reference number | TEXT | No |  | `account.csv` | 100000001 |
| `account_type` | Type of account | TEXT | No |  | `account.csv` | Chequing |
| `status` | Current status of this record | TEXT | No |  | `account.csv` | ACTIVE |
| `current_balance` | Current account balance | NUMERIC | No |  | `account.csv` | 2500.5 |
| `opened_date` | Account opening date | TEXT | No |  | `account.csv` | 2023-01-10 |

## complaint

Complaint details, current status and priority.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `complaint_id` | Complaint identifier | TEXT | Yes | PK | `complaint.csv` | CMP001 |
| `customer_id` | Customer identifier | TEXT | Yes | FK to customer.customer_id | `complaint.csv` | CUS001 |
| `account_id` | Account identifier | TEXT | No | FK to account.account_id | `complaint.csv` | ACC001 |
| `channel` | How the complaint was received | TEXT | No |  | `complaint.csv` | Phone |
| `category` | Complaint category | TEXT | Yes |  | `complaint.csv` | Fee Dispute |
| `complaint_text` | Complaint details | TEXT | No |  | `complaint.csv` | Unexpected overdraft fee |
| `priority` | Urgency of the complaint | TEXT | No |  | `complaint.csv` | High |
| `status` | Current status of this record | TEXT | Yes | OPEN / IN_PROGRESS / UNDER_REVIEW / CLOSED | `complaint.csv` | OPEN |
| `received_at` | Complaint received timestamp | TEXT | Yes |  | `complaint.csv` | 2025-01-01 09:00:00 |
| `assigned_analyst_id` | Assigned employee | TEXT | No | FK to employee.employee_id | `complaint.csv` | EMP001 |

## service_request

Customer service requests, not always linked to a complaint.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `request_id` | Request identifier | TEXT | Yes | PK | `service_request.csv` | SR001 |
| `customer_id` | Customer identifier | TEXT | No | FK to customer.customer_id | `service_request.csv` | CUS001 |
| `account_id` | Account identifier | TEXT | No | FK to account.account_id | `service_request.csv` | ACC001 |
| `request_type` | Type of service request | TEXT | No |  | `service_request.csv` | Address Change |
| `status` | Current status of this record | TEXT | No |  | `service_request.csv` | CLOSED |
| `created_at` | Creation timestamp | TEXT | No |  | `service_request.csv` | 2025-01-01 |
| `closed_at` | Close timestamp if recorded | TEXT | No |  | `service_request.csv` | 2025-01-02 |

## complaint_status_history

Past complaint status changes.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `history_id` | Status history identifier | INTEGER | Yes | PK | `complaint_status_history.csv` | 1 |
| `complaint_id` | Complaint identifier | TEXT | Yes | FK to complaint.complaint_id | `complaint_status_history.csv` | CMP001 |
| `old_status` | Previous complaint status | TEXT | No |  | `complaint_status_history.csv` | NULL |
| `new_status` | Updated complaint status | TEXT | Yes |  | `complaint_status_history.csv` | OPEN |
| `changed_by` | Employee who changed the status | TEXT | No | FK to employee.employee_id | `complaint_status_history.csv` | EMP001 |
| `changed_at` | Status change time | TEXT | Yes |  | `complaint_status_history.csv` | 2026-10-20 19:32:47 |
| `comments` | Notes on the status change | TEXT | No |  | `complaint_status_history.csv` | Complaint created |

## policy_document

Versioned policy documents.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `policy_id` | Policy identifier | TEXT | Yes | PK | `policy_document.csv` | POL001 |
| `policy_name` | Policy name | TEXT | No |  | `policy_document.csv` | Complaint Resolution Policy |
| `version_number` | Policy version | TEXT | No |  | `policy_document.csv` | 1.0 |
| `effective_date` | Policy start date | TEXT | No |  | `policy_document.csv` | 2024-01-01 |
| `status` | Current status of this record | TEXT | No |  | `policy_document.csv` | ACTIVE |

## policy_section

Text sections belonging to policy documents.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `section_id` | Policy section identifier | TEXT | Yes | PK | `policy_section.csv` | SEC001 |
| `policy_id` | Policy identifier | TEXT | No | FK to policy_document.policy_id | `policy_section.csv` | POL001 |
| `section_title` | Policy section heading | TEXT | No |  | `policy_section.csv` | Complaint Intake |
| `section_text` | Policy wording | TEXT | No |  | `policy_section.csv` | All complaints must be recorded. |

## transactions

Account transaction records.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `transaction_id` | Transaction identifier | TEXT | Yes | PK | `transactions.csv` | TXN001 |
| `account_id` | Account identifier | TEXT | No | FK to account.account_id | `transactions.csv` | ACC001 |
| `transaction_type` | Transaction type | TEXT | No |  | `transactions.csv` | DEBIT |
| `amount` | Monetary amount | NUMERIC | No |  | `transactions.csv` | 35 |
| `processed_at` | Transaction processing time | TEXT | No |  | `transactions.csv` | 2025-01-01 08:00:00 |
| `balance_before` | Balance before transaction | NUMERIC | No |  | `transactions.csv` | 2535.5 |
| `balance_after` | Balance after transaction | NUMERIC | No |  | `transactions.csv` | 2500.5 |
| `description` | Transaction description | TEXT | No |  | `transactions.csv` | ATM withdrawal |

## fee

Account fees and reversal flags.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `fee_id` | Fee identifier | TEXT | Yes | PK | `fee.csv` | FEE001 |
| `account_id` | Account identifier | TEXT | No | FK to account.account_id | `fee.csv` | ACC001 |
| `transaction_id` | Transaction identifier | TEXT | No | FK to transactions.transaction_id | `fee.csv` | TXN001 |
| `fee_type` | Fee category | TEXT | No |  | `fee.csv` | Overdraft |
| `amount` | Monetary amount | NUMERIC | No |  | `fee.csv` | 35 |
| `charged_at` | Fee charge time | TEXT | No |  | `fee.csv` | 2025-01-01 08:01:00 |
| `reversed_flag` | Whether fee was reversed | INTEGER | No | 0 or 1 | `fee.csv` | 0 |

## investigation

Complaint investigations carried out by employees.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `investigation_id` | Investigation identifier | TEXT | Yes | PK | `investigation.csv` | INV001 |
| `complaint_id` | Complaint identifier | TEXT | No | FK to complaint.complaint_id | `investigation.csv` | CMP001 |
| `analyst_id` | Assigned analyst | TEXT | No | FK to employee.employee_id | `investigation.csv` | EMP001 |
| `started_at` | Investigation start time | TEXT | No |  | `investigation.csv` | 2025-01-02 |
| `completed_at` | Investigation end time | TEXT | No |  | `investigation.csv` | 2025-01-04 |
| `investigation_summary` | Investigation findings | TEXT | No |  | `investigation.csv` | Overdraft fee verified |

## recommendation

Proposed resolutions for investigations.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `recommendation_id` | Recommendation identifier | TEXT | Yes | PK | `recommendation.csv` | REC001 |
| `investigation_id` | Investigation identifier | TEXT | No | FK to investigation.investigation_id | `recommendation.csv` | INV001 |
| `recommendation_text` | Proposed outcome | TEXT | No |  | `recommendation.csv` | Reverse overdraft fee |
| `confidence_score` | Recorded confidence score | NUMERIC | No |  | `recommendation.csv` | 95.5 |
| `generated_at` | Recommendation creation time | TEXT | No |  | `recommendation.csv` | 2026-10-20 19:32:47 |

## review_request

Requests for human review of recommendations.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `review_request_id` | Review request identifier | TEXT | Yes | PK | `review_request.csv` | RR001 |
| `complaint_id` | Complaint identifier | TEXT | No | FK to complaint.complaint_id | `review_request.csv` | CMP001 |
| `recommendation_id` | Recommendation identifier | TEXT | No | FK to recommendation.recommendation_id | `review_request.csv` | REC001 |
| `reviewer_id` | Employee who reviews the request | TEXT | No | FK to employee.employee_id | `review_request.csv` | EMP003 |
| `requested_at` | When review was requested | TEXT | No |  | `review_request.csv` | 2026-10-20 19:32:47 |
| `status` | Current status of this record | TEXT | No |  | `review_request.csv` | PENDING |

## review_decision

Reviewers' decisions about requests.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `decision_id` | Review decision identifier | TEXT | Yes | PK | `review_decision.csv` | DEC001 |
| `review_request_id` | Review request identifier | TEXT | No | FK to review_request.review_request_id | `review_decision.csv` | RR001 |
| `decision` | Review outcome | TEXT | No |  | `review_decision.csv` | APPROVED |
| `decision_reason` | Reason for decision | TEXT | No |  | `review_decision.csv` | Valid fee dispute |
| `decision_date` | Date of decision | TEXT | No |  | `review_decision.csv` | 2026-10-20 19:32:47 |

## customer_response

Responses to customers, including approval and send date.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `response_id` | Customer response identifier | TEXT | Yes | PK | `customer_response.csv` | RES001 |
| `complaint_id` | Complaint identifier | TEXT | No | FK to complaint.complaint_id | `customer_response.csv` | CMP001 |
| `response_text` | Message sent to customer | TEXT | No |  | `customer_response.csv` | Your fee has been reversed. |
| `approved_by` | Employee who approved response | TEXT | No | FK to employee.employee_id | `customer_response.csv` | EMP003 |
| `sent_date` | When response was sent | TEXT | No |  | `customer_response.csv` | 2025-01-05 |

## audit_log

Recorded actions and events. Not an automatic audit trigger.

| Column | Purpose | Type | Required? | Key / rule | Source | Example |
|---|---|---|---|---|---|---|
| `audit_id` | Audit event identifier | INTEGER | Yes | PK | `audit_log.csv` | 1 |
| `entity_name` | Entity type affected | TEXT | No |  | `audit_log.csv` | COMPLAINT |
| `entity_id` | Identifier of affected record | TEXT | No |  | `audit_log.csv` | CMP001 |
| `action_type` | Kind of action | TEXT | No |  | `audit_log.csv` | CREATE |
| `performed_by` | Employee who performed action | TEXT | No | FK to employee.employee_id | `audit_log.csv` | EMP001 |
| `event_timestamp` | Event time | TEXT | No |  | `audit_log.csv` | 2026-10-20 19:32:47 |
| `details` | Details of the event | TEXT | No |  | `audit_log.csv` | Complaint created |

