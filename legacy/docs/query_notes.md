# Query notes

- `status = 'OPEN'` only shows complaints currently open.
- Filter dates using `>=` for the start and `<` for the day after the end.
- `LEFT JOIN account` keeps complaints that have no account ID.
- SQLite uses `strftime` and `julianday` for dates.
- Complaint closure dates are not in the original `complaint` table.
