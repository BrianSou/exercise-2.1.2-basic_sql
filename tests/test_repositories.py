from sqlalchemy.exc import IntegrityError
import tempfile
import unittest
from pathlib import Path
from legacy.build_database import seed
from src.data.database_manager import DatabaseManager
from src.data.customer_repository import CustomerRepository
from src.data.account_repository import AccountRepository
from src.data.complaint_repository import ComplaintRepository

class RepositoriesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'test.db'
        seed(self.path)
        db = DatabaseManager(self.path)
        self.customer = CustomerRepository(db)
        self.account = AccountRepository(db)
        self.complaint = ComplaintRepository(db)

    def tearDown(self): self.tmp.cleanup()

    def test_customer_found(self): self.assertEqual(self.customer.get_by_id('CUS001')['customer_id'], 'CUS001')
    def test_customer_missing(self): self.assertIsNone(self.customer.get_by_id('missing'))
    def test_accounts(self): self.assertTrue(self.account.get_for_customer('CUS001'))
    def test_accounts_missing(self): self.assertEqual(self.account.get_for_customer('missing'), [])
    def test_complaints(self): self.assertTrue(self.complaint.get_for_customer('CUS001'))
    def test_complaint_missing(self): self.assertIsNone(self.complaint.get_by_id('missing'))
    def test_sql_injection_is_safe(self):
        self.assertIsNone(self.customer.get_by_id("CUS001' OR 1=1 --"))
    def test_insert_and_duplicate_rollback(self):
        row = dict(complaint_id='CMP999', customer_id='CUS001', account_id='ACC001',
                   channel='Email', category='Fee Dispute', complaint_text='Test fee',
                   priority='High', status='OPEN', received_at='2026-10-28 09:00:00',
                   assigned_analyst_id=None)
        self.assertEqual(self.complaint.create(row)['complaint_id'], 'CMP999')
        with self.assertRaises(IntegrityError): self.complaint.create(row)
        self.assertEqual(len([x for x in self.complaint.get_for_customer('CUS001') if x['complaint_id']=='CMP999']),1)
    def test_foreign_key(self):
        row = dict(complaint_id='CMP998', customer_id='MISSING', account_id=None,
                   channel='Email', category='Fee Dispute', complaint_text='Test fee',
                   priority='High', status='OPEN', received_at='2026-10-28 09:00:00',
                   assigned_analyst_id=None)
        with self.assertRaises(IntegrityError): self.complaint.create(row)
    def test_missing_fields(self):
        with self.assertRaises(ValueError): self.complaint.create({'complaint_id':'CMP999'})

if __name__ == '__main__': unittest.main()
