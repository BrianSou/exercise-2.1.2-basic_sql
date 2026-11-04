"""Build the column-level dictionary from the working SQLite database."""
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
TABLE_PURPOSE = {
    "customer": "People who submit complaints and hold accounts.",
    "employee": "Bank employees handling complaints and reviews.",
    "account": "Accounts owned by customers.",
    "complaint": "Complaint details, current status and priority.",
    "service_request": "Customer service requests, not always linked to a complaint.",
    "complaint_status_history": "Past complaint status changes.",
    "policy_document": "Versioned policy documents.",
    "policy_section": "Text sections belonging to policy documents.",
    "transactions": "Account transaction records.",
    "fee": "Account fees and reversal flags.",
    "investigation": "Complaint investigations carried out by employees.",
    "recommendation": "Proposed resolutions for investigations.",
    "review_request": "Requests for human review of recommendations.",
    "review_decision": "Reviewers' decisions about requests.",
    "customer_response": "Responses to customers, including approval and send date.",
    "audit_log": "Recorded actions and events. Not an automatic audit trigger.",
}

COLUMN_PURPOSE = {
    'customer_id': 'Customer identifier', 'account_id': 'Account identifier',
    'complaint_id': 'Complaint identifier', 'request_id': 'Request identifier',
    'history_id': 'Status history identifier', 'first_name': 'First name',
    'last_name': 'Last name', 'email': 'Email address', 'phone_number': 'Phone number',
    'segment': 'Customer segment', 'date_created': 'Record creation date',
    'account_number': 'Account reference number', 'account_type': 'Type of account',
    'status': 'Current status of this record', 'current_balance': 'Current account balance',
    'opened_date': 'Account opening date', 'channel': 'How the complaint was received',
    'category': 'Complaint category', 'complaint_text': 'Complaint details',
    'priority': 'Urgency of the complaint', 'received_at': 'Complaint received timestamp',
    'assigned_analyst_id': 'Assigned employee', 'request_type': 'Type of service request',
    'created_at': 'Creation timestamp', 'closed_at': 'Close timestamp if recorded',
    'old_status': 'Previous complaint status', 'new_status': 'Updated complaint status',
    'changed_by': 'Employee who changed the status', 'changed_at': 'Status change time',
    'comments': 'Notes on the status change', 'policy_id': 'Policy identifier',
    'policy_name': 'Policy name', 'version_number': 'Policy version',
    'effective_date': 'Policy start date', 'section_id': 'Policy section identifier',
    'section_title': 'Policy section heading', 'section_text': 'Policy wording',
    'transaction_id': 'Transaction identifier', 'transaction_type': 'Transaction type',
    'amount': 'Monetary amount', 'processed_at': 'Transaction processing time',
    'balance_before': 'Balance before transaction', 'balance_after': 'Balance after transaction',
    'description': 'Transaction description', 'fee_id': 'Fee identifier',
    'fee_type': 'Fee category', 'charged_at': 'Fee charge time',
    'reversed_flag': 'Whether fee was reversed',
    'investigation_id': 'Investigation identifier', 'analyst_id': 'Assigned analyst',
    'started_at': 'Investigation start time', 'completed_at': 'Investigation end time',
    'investigation_summary': 'Investigation findings',
    'recommendation_id': 'Recommendation identifier',
    'recommendation_text': 'Proposed outcome', 'confidence_score': 'Recorded confidence score',
    'generated_at': 'Recommendation creation time', 'review_request_id': 'Review request identifier',
    'reviewer_id': 'Employee who reviews the request',
    'requested_at': 'When review was requested', 'decision_id': 'Review decision identifier',
    'decision': 'Review outcome', 'decision_reason': 'Reason for decision',
    'decision_date': 'Date of decision', 'response_id': 'Customer response identifier',
    'response_text': 'Message sent to customer', 'approved_by': 'Employee who approved response',
    'sent_date': 'When response was sent', 'audit_id': 'Audit event identifier',
    'entity_name': 'Entity type affected', 'entity_id': 'Identifier of affected record',
    'action_type': 'Kind of action', 'performed_by': 'Employee who performed action',
    'event_timestamp': 'Event time', 'details': 'Details of the event',
    'role': 'Employee role',
}


def build(db_path, output=None):
    output = Path(output or HERE / 'docs' / 'data_dictionary.md')
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '# Data dictionary', '',
        'Source: original banking complaint CSV files. Database: `data/original.db` (SQLite).',
        'One row in `complaint` represents one complaint. Missing optional CSV values are NULL.',
        '', '## Modeling notes', '',
        '- Each complaint needs a customer. An account is optional.',
        '- One customer can have multiple accounts and complaints.',
        '- A complaint can have multiple status-history entries.',
        '- Category and priority are stored as text. There are no separate lookup tables.',
        '- Status-history and audit-log rows are imported data. The database does not automatically write a new audit row for every change.',
        '- The supplied `service_request.csv` has no `complaint_id`. Requests can be linked to customers and accounts, but not directly to a complaint in this schema.',
        '- The original complaint table does not have a closure date.',
        '',
    ]
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for table in TABLE_PURPOSE:
            cols = list(conn.execute(f'PRAGMA table_info("{table}")'))
            fks = {r['from']: r for r in conn.execute(f'PRAGMA foreign_key_list("{table}")')}
            sample = conn.execute(f'SELECT * FROM "{table}" LIMIT 1').fetchone()
            lines += [f'## {table}', '', TABLE_PURPOSE[table], '',
                      '| Column | Purpose | Type | Required? | Key / rule | Source | Example |',
                      '|---|---|---|---|---|---|---|']
            for c in cols:
                name = c['name']
                raw = sample[name] if sample else None
                example = 'NULL' if raw is None else str(raw).replace('|', '\\|').replace('\n', ' ')
                if len(example) > 50: example=example[:47]+'...'
                constraints = []
                if c['pk']: constraints.append('PK')
                if name in fks: constraints.append('FK to '+fks[name]['table']+'.'+fks[name]['to'])
                if table == 'complaint' and name == 'status': constraints.append('OPEN / IN_PROGRESS / UNDER_REVIEW / CLOSED')
                if table == 'fee' and name == 'reversed_flag': constraints.append('0 or 1')
                required = 'Yes' if c['notnull'] or c['pk'] else 'No'
                lines.append(f'| `{name}` | {COLUMN_PURPOSE.get(name, name.replace("_", " ").capitalize())} | {c["type"]} | {required} | {"; ".join(constraints) if constraints else ""} | `{table}.csv` | {example} |')
            lines.append('')
    output.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return output

if __name__ == '__main__':
    build(HERE.parent / 'data' / 'original.db')
