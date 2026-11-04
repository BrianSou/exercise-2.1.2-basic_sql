"""Checks the joins, aging examples and definitions from the question sheets."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from legacy.build_database import seed
from legacy.build_data_dictionary import build, TABLE_PURPOSE

ROOT = Path(__file__).resolve().parents[1]

class RequirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / 'original.db'
        seed(cls.db_path)
        cls.conn = sqlite3.connect(cls.db_path)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.tmp.cleanup()

    def test_join_questions(self):
        sql = (ROOT / 'legacy/sql/join_queries.sql').read_text(encoding='utf-8')
        statements = [part for part in sql.split(';') if part.strip()]
        self.assertEqual(len(statements), 4)
        names = self.conn.execute(statements[0]).fetchall()
        self.assertEqual(len(names), 30)
        self.assertTrue(all(row['customer_name'].strip() for row in names))
        accounts = self.conn.execute(statements[1]).fetchall()
        self.assertEqual(len(accounts), 30)
        self.assertTrue(any(row['account_type'] is None for row in accounts))
        checks = self.conn.execute(statements[2]).fetchone()
        self.assertEqual(tuple(checks), (30, 30, 30))
        missing = self.conn.execute(statements[3]).fetchall()
        expected = self.conn.execute('SELECT COUNT(*) FROM complaint WHERE account_id IS NULL').fetchone()[0]
        self.assertEqual(len(missing), expected)

    def test_metric_queries_run(self):
        sql = (ROOT / 'legacy/sql/complaint_metrics.sql').read_text(encoding='utf-8')
        statements = [p for p in sql.split(';') if p.strip() and not p.strip().startswith('-- Closed-case')]
        # Comments may come before the SELECT. SQLite can execute those directly.
        outputs = [self.conn.execute(p).fetchall() for p in statements]
        self.assertEqual(sum(r['complaint_count'] for r in outputs[0]), 30)
        self.assertEqual(sum(r['complaint_count'] for r in outputs[1]), 30)
        self.assertEqual(sum(r['complaint_count'] for r in outputs[2]), 30)
        self.assertEqual(outputs[3][0][0], self.conn.execute("SELECT COUNT(*) FROM complaint WHERE status != 'CLOSED'").fetchone()[0])
        self.assertEqual(outputs[5][0][0], 10)

    def test_analyst_view_has_no_unneeded_names_or_emails(self):
        cols = [row[1] for row in self.conn.execute('PRAGMA table_info(complaint_analyst_view)')]
        self.assertNotIn('email', cols)
        self.assertNotIn('first_name', cols)
        self.assertNotIn('last_name', cols)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM complaint_analyst_view').fetchone()[0], 30)

    def test_advanced_questions_run(self):
        sql = (ROOT / 'legacy/sql/advanced_queries.sql').read_text(encoding='utf-8')
        statements = [part for part in sql.split(';') if part.strip()]
        self.assertGreaterEqual(len(statements), 5)
        for statement in statements:
            self.conn.execute(statement).fetchall()
        boundary = next(statement for statement in statements if 'boundary_dates AS' in statement)
        rows = self.conn.execute(boundary).fetchall()
        actual = {r['age_days']:r['age_bucket'] for r in rows}
        self.assertEqual(actual,{7:'0-7 days',8:'8-30 days',30:'8-30 days',31:'31+ days'})

    def test_all_dictionary_columns_documented(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = build(self.db_path,Path(tmp)/'dict.md').read_text(encoding='utf-8')
            for table in TABLE_PURPOSE:
                self.assertIn('## '+table+'\n',content)
                for col in self.conn.execute(f'PRAGMA table_info("{table}")'):
                    self.assertIn('| `'+col['name']+'` |',content)
            self.assertIn('Source',content)
            self.assertIn('Required?',content)

    def test_sql_rejects_null_customer_primary_key(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.conn:
                self.conn.execute('INSERT INTO customer(customer_id,first_name,last_name) VALUES(NULL,?,?)', ('A','B'))

    def test_original_resolution_date_not_available(self):
        cols = [row[1] for row in self.conn.execute('PRAGMA table_info(complaint)')]
        self.assertNotIn('closed_at',cols)
        self.assertNotIn('date_closed',cols)

    def test_bulk_closed_case_sql(self):
        db=ROOT/'data/bulk.db'
        if not db.exists(): self.skipTest('Run setup_local.py to create bulk.db first')
        with sqlite3.connect(db) as con:
            result=con.execute((ROOT/'bulk/sql/closed_case_resolution.sql').read_text()).fetchall()
            self.assertTrue(result)
            self.assertTrue(all(row[1]>0 and row[2]>=0 for row in result))

if __name__=='__main__':
    unittest.main()
