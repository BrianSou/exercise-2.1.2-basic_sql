-- SQLite schema for the original 30-row banking complaint dataset.
PRAGMA foreign_keys = ON;

CREATE TABLE customer (
  customer_id TEXT NOT NULL PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT,
  phone_number TEXT,
  segment TEXT,
  date_created TEXT
);

CREATE TABLE employee (
  employee_id TEXT NOT NULL PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT,
  role TEXT
);

CREATE TABLE account (
  account_id TEXT NOT NULL PRIMARY KEY,
  customer_id TEXT NOT NULL REFERENCES customer(customer_id),
  account_number TEXT,
  account_type TEXT,
  status TEXT,
  current_balance NUMERIC,
  opened_date TEXT
);

CREATE TABLE complaint (
  complaint_id TEXT NOT NULL PRIMARY KEY,
  customer_id TEXT NOT NULL REFERENCES customer(customer_id),
  account_id TEXT REFERENCES account(account_id),
  channel TEXT,
  category TEXT NOT NULL,
  complaint_text TEXT,
  priority TEXT,
  status TEXT NOT NULL CHECK (status IN ('OPEN','IN_PROGRESS','UNDER_REVIEW','CLOSED')),
  received_at TEXT NOT NULL,
  assigned_analyst_id TEXT REFERENCES employee(employee_id)
);

CREATE TABLE service_request (
  request_id TEXT NOT NULL PRIMARY KEY,
  customer_id TEXT REFERENCES customer(customer_id),
  account_id TEXT REFERENCES account(account_id),
  request_type TEXT,
  status TEXT,
  created_at TEXT,
  closed_at TEXT
);

CREATE TABLE complaint_status_history (
  history_id INTEGER PRIMARY KEY,
  complaint_id TEXT NOT NULL REFERENCES complaint(complaint_id),
  old_status TEXT,
  new_status TEXT NOT NULL,
  changed_by TEXT REFERENCES employee(employee_id),
  changed_at TEXT NOT NULL,
  comments TEXT
);

CREATE TABLE policy_document (
  policy_id TEXT NOT NULL PRIMARY KEY,
  policy_name TEXT,
  version_number TEXT,
  effective_date TEXT,
  status TEXT
);

CREATE TABLE policy_section (
  section_id TEXT NOT NULL PRIMARY KEY,
  policy_id TEXT REFERENCES policy_document(policy_id),
  section_title TEXT,
  section_text TEXT
);

CREATE TABLE transactions (
  transaction_id TEXT NOT NULL PRIMARY KEY,
  account_id TEXT REFERENCES account(account_id),
  transaction_type TEXT,
  amount NUMERIC,
  processed_at TEXT,
  balance_before NUMERIC,
  balance_after NUMERIC,
  description TEXT
);

CREATE TABLE fee (
  fee_id TEXT NOT NULL PRIMARY KEY,
  account_id TEXT REFERENCES account(account_id),
  transaction_id TEXT REFERENCES transactions(transaction_id),
  fee_type TEXT,
  amount NUMERIC,
  charged_at TEXT,
  reversed_flag INTEGER CHECK (reversed_flag IN (0,1))
);

CREATE TABLE investigation (
  investigation_id TEXT NOT NULL PRIMARY KEY,
  complaint_id TEXT REFERENCES complaint(complaint_id),
  analyst_id TEXT REFERENCES employee(employee_id),
  started_at TEXT,
  completed_at TEXT,
  investigation_summary TEXT
);

CREATE TABLE recommendation (
  recommendation_id TEXT NOT NULL PRIMARY KEY,
  investigation_id TEXT REFERENCES investigation(investigation_id),
  recommendation_text TEXT,
  confidence_score NUMERIC,
  generated_at TEXT
);

CREATE TABLE review_request (
  review_request_id TEXT NOT NULL PRIMARY KEY,
  complaint_id TEXT REFERENCES complaint(complaint_id),
  recommendation_id TEXT REFERENCES recommendation(recommendation_id),
  reviewer_id TEXT REFERENCES employee(employee_id),
  requested_at TEXT,
  status TEXT
);

CREATE TABLE review_decision (
  decision_id TEXT NOT NULL PRIMARY KEY,
  review_request_id TEXT REFERENCES review_request(review_request_id),
  decision TEXT,
  decision_reason TEXT,
  decision_date TEXT
);

CREATE TABLE customer_response (
  response_id TEXT NOT NULL PRIMARY KEY,
  complaint_id TEXT REFERENCES complaint(complaint_id),
  response_text TEXT,
  approved_by TEXT REFERENCES employee(employee_id),
  sent_date TEXT
);

CREATE TABLE audit_log (
  audit_id INTEGER PRIMARY KEY,
  entity_name TEXT,
  entity_id TEXT,
  action_type TEXT,
  performed_by TEXT REFERENCES employee(employee_id),
  event_timestamp TEXT,
  details TEXT
);

CREATE INDEX idx_complaint_customer ON complaint(customer_id);
CREATE INDEX idx_complaint_status ON complaint(status);
CREATE INDEX idx_history_complaint ON complaint_status_history(complaint_id, changed_at);
