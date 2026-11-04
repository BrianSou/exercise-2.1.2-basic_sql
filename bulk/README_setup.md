# Bulk database setup

Run from the repository root:

```powershell
python bulk/seed_database.py --data-dir bulk/data --db data/bulk.db
```

If the bulk database already exists and you want to replace its contents, add `--reset`. Do not use that option on a database you need to keep.

Expected: 100 customers, 150 accounts, 120 complaints, and 5 sample service requests.
The five service requests are examples added because the official matching request file was not provided.

The seeder checks CSV headers, IDs, account ownership, foreign keys, and totals. The log and integrity files are saved to `bulk/data/`; `setup_local.py` copies them into `bulk/outputs/`.

SQLite needs no extra packages. The optional PostgreSQL backend was not tested with a live server.
