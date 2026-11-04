# Failure Test Results

I ran the script with the original CSV and tested these cases.

## 1. Normal file

Command: `python complaint_analysis.py`

Result: Passed. It read 120 complaints, skipped 0 rows and created both output files.

## 2. Missing file

Command: `python complaint_analysis.py no_such_file.csv`

Result: Passed. The script stopped with exit code 1 and printed:

```text
Error: File not found: /tmp/tmpivvmm_nt/no_such_file.csv
```

It did not crash with a Python traceback.

## 3. Incomplete rows

I made a test copy of the CSV and removed the category from `CP00001` and the closed date from `CP00003` (which has status `Closed`). The original CSV was not changed.

Result: Passed. The script printed:

```text
Warning: Row 2 has missing details. Skipping it.
Warning: Row 4 is Closed but has no closed date.
Valid complaints: 119; skipped rows: 1
```

The output counted 119 valid complaints and 1 skipped row. The closed complaint still counted toward its status/category, but it was left out of the average resolution time because its closed date was missing.

## 4. Missing required column

I made a separate test copy with the `status` column removed.

Result: Passed. The script stopped with exit code 1 and printed:

```text
Error: Missing required columns: status
```

## 5. Exercise date column names

I also renamed `date_opened` and `date_closed` to `created_date` and `resolved_date` in a test copy.

Result: Passed. The script accepted both naming formats and still read 120 complaints.

## Notes

- All tests were run against the actual script. Test copies were kept separate from the original data.
- Blank closed dates are normal for unresolved complaints.
- A Closed complaint without a usable closed date is counted as Closed, but not included in the resolution-time average.
