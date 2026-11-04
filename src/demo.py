"""Example of reading the original banking data."""
from src.data.database_manager import DatabaseManager
from src.data.customer_repository import CustomerRepository
from src.data.account_repository import AccountRepository
from src.data.complaint_repository import ComplaintRepository

if __name__ == '__main__':
    db = DatabaseManager()
    print('Customer:', CustomerRepository(db).get_by_id('CUS001'))
    print('Accounts:', len(AccountRepository(db).get_for_customer('CUS001')))
    print('Complaints:', len(ComplaintRepository(db).get_for_customer('CUS001')))
