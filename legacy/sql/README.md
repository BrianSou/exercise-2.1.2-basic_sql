# SQL files

Open `data/original.db` in DBeaver. All SQL files in this folder use SQLite syntax.

- `database_schema.sql` is the clean database schema. Do not rerun it against tables that already exist.
- `basic_queries.sql` answers basic questions.
- `join_queries.sql` verifies customer/account joins.
- `complaint_analyst_view.sql` defines the one-row-per-complaint view (already created by setup).
- `complaint_metrics.sql` calculates counts and backlog.
- `advanced_queries.sql` has age buckets, repeat customers, latest status, and ranking.

The SQL scripts operate on the **original 30-complaint dataset** and not on `data/bulk.db`.
