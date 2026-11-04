"""Create the original banking complaints database from the 16 supplied CSVs."""
import csv
import sqlite3
from pathlib import Path
import os

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / 'data'
SCHEMA = HERE / 'sql' / 'database_schema.sql'
TABLES = ['customer', 'employee', 'account', 'complaint', 'service_request',
          'complaint_status_history', 'policy_document', 'policy_section',
          'transactions', 'fee', 'investigation', 'recommendation',
          'review_request', 'review_decision', 'customer_response', 'audit_log']


def seed(db_path, reset=False):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not reset:
        raise FileExistsError(f'{path} already exists. Use --reset to replace it.')

    # Build in a temporary file first, so a failed run does not damage the old DB.
    temporary = path.with_suffix('.building.db')
    if temporary.exists():
        temporary.unlink()
    con = sqlite3.connect(temporary)
    try:
        con.execute('PRAGMA foreign_keys = ON')
        con.executescript(SCHEMA.read_text(encoding='utf-8'))
        counts = {}
        for table in TABLES:
            with (DATA_DIR / (table + '.csv')).open(encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                db_cols = [r[1] for r in con.execute(f'PRAGMA table_info({table})')]
                if set(reader.fieldnames or []) != set(db_cols):
                    raise ValueError(f'Wrong CSV columns for {table}')
                placeholders = ', '.join('?' for _ in db_cols)
                names = ', '.join(db_cols)
                query = f'INSERT INTO {table} ({names}) VALUES ({placeholders})'
                con.executemany(query, [[r[col] or None for col in db_cols] for r in rows])
                counts[table] = len(rows)
        # A complaint's optional account must belong to its customer.
        wrong_owner = con.execute("""SELECT COUNT(*) FROM complaint c JOIN account a
          ON a.account_id = c.account_id WHERE c.customer_id <> a.customer_id""").fetchone()[0]
        wrong_request_owner = con.execute("""SELECT COUNT(*) FROM service_request r JOIN account a
          ON a.account_id = r.account_id WHERE r.customer_id <> a.customer_id""").fetchone()[0]
        fk_errors = con.execute('PRAGMA foreign_key_check').fetchall()
        if wrong_owner or wrong_request_owner or fk_errors:
            raise ValueError(f'Integrity errors: owners={wrong_owner + wrong_request_owner}, FK={len(fk_errors)}')
        for table, expected in counts.items():
            actual = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            if actual != expected:
                raise ValueError('Row count changed during load: ' + table)
        con.execute("""CREATE VIEW complaint_analyst_view AS
           SELECT c.complaint_id, c.customer_id, c.account_id, c.category,
                  c.priority, c.status, c.received_at, c.channel,
                  a.account_type, a.status AS account_status, u.segment AS customer_segment
           FROM complaint c JOIN customer u ON u.customer_id = c.customer_id
           LEFT JOIN account a ON a.account_id = c.account_id""")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        temporary.unlink(missing_ok=True)
        raise
    else:
        con.close()
        os.replace(temporary, path)
    return counts

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--db', default=str(HERE.parent / 'data' / 'original.db'))
    p.add_argument('--reset', action='store_true')
    a = p.parse_args()
    for name, count in seed(a.db, reset=a.reset).items():
        print(f'{name}: {count}')
