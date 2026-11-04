# Local verification

Tested the repository from a fresh copied folder after deleting both `.db` files.

- `python setup_local.py`: passed. Rebuilt both databases and refreshed the reports.
- `data/original.db`: 30 complaints; no foreign-key errors.
- `data/bulk.db`: 120 complaints; no foreign-key errors.
- `python -m unittest discover -s tests -v`: 20 tests passed.
- `python -m unittest discover -s bulk/tests -v`: 13 tests passed.
- The bulk tests deliberately simulate a transaction failure. The printed `ERROR: test failure` message is from that test; the test runner itself reports `OK`.

The SQLite local setup is verified. PostgreSQL was not tested. The approved Week 1 specification was not supplied.
