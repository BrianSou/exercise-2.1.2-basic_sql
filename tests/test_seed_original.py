import sqlite3
import tempfile
import unittest
from pathlib import Path
from legacy.build_database import seed

class OriginalSeederTest(unittest.TestCase):
    def test_counts_and_foreign_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'original.db'
            counts = seed(db)
            self.assertEqual(counts['complaint'], 30)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute('SELECT COUNT(*) FROM complaint_analyst_view').fetchone()[0],30)
                self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_reset_requires_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'original.db'; seed(db)
            with self.assertRaises(FileExistsError): seed(db)
            self.assertEqual(seed(db,reset=True)['complaint'],30)

if __name__ == '__main__': unittest.main()
