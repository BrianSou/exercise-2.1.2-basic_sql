"""Read complaints.csv and write a CSV report and a short Markdown summary.

Run: python complaint_analysis.py
Or:  python complaint_analysis.py path/to/complaints.csv
"""

import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path


UNRESOLVED_STATUSES = {"Open", "In Review", "Escalated"}


def analyze(file_path, output_dir=None):
    # 1. Read the file.
    try:
        with file_path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames or []
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return 1
    except OSError as error:
        print(f"Error: Could not read file: {error}")
        return 1

    # The exercise calls these created_date and resolved_date.
    # The supplied CSV calls them date_opened and date_closed.
    opened_col = "created_date" if "created_date" in columns else "date_opened"
    closed_col = "resolved_date" if "resolved_date" in columns else "date_closed"
    required = ["complaint_id", "customer_id", "category", "status", opened_col, closed_col]
    missing_columns = [column for column in required if column not in columns]

    if missing_columns:
        print("Error: Missing required columns: " + ", ".join(missing_columns))
        return 1

    # 2. Check for empty fields and unusable rows.
    missing_values = {
        column: sum(not (row.get(column) or "").strip() for row in rows)
        for column in columns
    }
    print(f"Loaded {len(rows)} rows from {file_path.name}")
    print("Missing values:")
    for column, count in missing_values.items():
        print(f"  {column}: {count}")

    valid_rows = []
    skipped = 0
    missing_closure_dates = 0
    seen_ids = set()

    for line_number, row in enumerate(rows, start=2):
        # An unresolved complaint normally has no closed date, so it is optional here.
        needed = ["complaint_id", "customer_id", "category", "status", opened_col]
        if any(not (row.get(column) or "").strip() for column in needed):
            print(f"Warning: Row {line_number} has missing details. Skipping it.")
            skipped += 1
            continue

        complaint_id = row["complaint_id"].strip()
        if complaint_id in seen_ids:
            print(f"Warning: Row {line_number} repeats complaint {complaint_id}. Skipping it.")
            skipped += 1
            continue

        try:
            opened = date.fromisoformat(row[opened_col].strip())
        except ValueError:
            print(f"Warning: Row {line_number} has an invalid opened date. Skipping it.")
            skipped += 1
            continue

        seen_ids.add(complaint_id)
        category = row["category"].strip()
        status = row["status"].strip()
        customer = row["customer_id"].strip()
        closed = None

        if status == "Closed":
            closed_text = (row.get(closed_col) or "").strip()
            if closed_text:
                try:
                    closed = date.fromisoformat(closed_text)
                    if closed < opened:
                        print(f"Warning: Row {line_number} closes before it opens. Ignoring resolution time.")
                        closed = None
                except ValueError:
                    print(f"Warning: Row {line_number} has an invalid closed date. Ignoring resolution time.")
            else:
                print(f"Warning: Row {line_number} is Closed but has no closed date.")
            if closed is None:
                missing_closure_dates += 1

        valid_rows.append((category, status, customer, opened, closed))

    # 3. Calculate the numbers.
    total = len(valid_rows)
    status_counts = Counter(row[1] for row in valid_rows)
    category_counts = Counter(row[0] for row in valid_rows)
    month_counts = Counter(row[3].strftime("%Y-%m") for row in valid_rows)
    customers = len({row[2] for row in valid_rows})
    backlog = sum(row[1] in UNRESOLVED_STATUSES for row in valid_rows)

    top_category = max(category_counts, key=category_counts.get) if total else "None"
    top_percent = category_counts[top_category] / total * 100 if total else 0

    resolution_days = {}
    for category in category_counts:
        days = [
            (closed - opened).days
            for cat, status, _, opened, closed in valid_rows
            if cat == category and status == "Closed" and closed is not None
        ]
        resolution_days[category] = days

    # 4. Save the measures to one CSV file.
    output_rows = [
        ("total_complaints", "", total),
        ("unresolved_backlog", "", backlog),
        ("distinct_customers", "", customers),
        ("top_category", "", top_category),
        ("top_category_percentage", "", f"{top_percent:.2f}"),
        ("skipped_rows", "", skipped),
        ("closed_cases_without_valid_resolution_date", "", missing_closure_dates),
    ]
    output_rows += [("status_count", status, count) for status, count in sorted(status_counts.items())]
    output_rows += [("category_count", category, count) for category, count in category_counts.most_common()]
    output_rows += [("opened_month_count", month, count) for month, count in sorted(month_counts.items())]
    for category in sorted(category_counts):
        days = resolution_days[category]
        average = f"{sum(days) / len(days):.2f}" if days else "N/A"
        output_rows.append(("closed_cases_with_valid_dates", category, len(days)))
        output_rows.append(("average_resolution_days", category, average))
    output_rows += [("missing_values", column, count) for column, count in missing_values.items()]

    output_dir = Path(output_dir) if output_dir else file_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "complaint_analysis_output.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "group", "value"])
        writer.writerows(output_rows)

    # 5. Save a short summary for the reader.
    report = [
        "# Complaint Analysis Summary", "",
        f"Analyzed **{total} complaints** from `{file_path.name}`. {skipped} rows were skipped.", "",
        "## Main results", "",
        f"- **Total complaints:** {total}",
        f"- **Unresolved complaints:** {backlog} (Open, In Review or Escalated)",
        f"- **Distinct customers:** {customers}",
        f"- **Most common category:** {top_category} ({category_counts[top_category]} complaints, {top_percent:.2f}%)" if total else "- No valid complaints found.",
        "", "## Complaints by status", "",
        "| Status | Count |", "|---|---:|",
    ]
    report += [f"| {status} | {count} |" for status, count in sorted(status_counts.items())]
    report += ["", "## Complaints by category", "", "| Category | Count |", "|---|---:|"]
    report += [f"| {category} | {count} |" for category, count in category_counts.most_common()]
    report += ["", "## Average resolution days by category", "",
               "This only uses Closed complaints with valid opened and closed dates.", "",
               "| Category | Closed cases used | Avg. days |", "|---|---:|---:|"]
    for category in sorted(category_counts):
        days = resolution_days[category]
        average = f"{sum(days) / len(days):.2f}" if days else "N/A"
        report.append(f"| {category} | {len(days)} | {average} |")

    report += ["", "## Complaints by opened month", "", "| Month | Count |", "|---|---:|"]
    report += [f"| {month} | {count} |" for month, count in sorted(month_counts.items())]
    report += ["", "## Data checks and notes", "",
               f"- {len(rows)} source rows were read; {skipped} incomplete, duplicate or invalid rows were skipped.",
               f"- {missing_closure_dates} Closed complaints did not have a valid closure date for the average.",
               f"- {missing_values[closed_col]} blank {closed_col} values were found. This is normal for cases that are not closed.",
               f"- Missing values were counted for every column in the output CSV.",
               f"- `{opened_col}` is treated as the complaint start date and `{closed_col}` as the closure date.",
               "- Resolution days = closure date minus start date. Unresolved complaints are excluded from the average.",
               "- Status and category counts reflect this CSV, not historical changes.",
               "- This CSV does not show separate escalation decisions, so it cannot measure the escalation-decision backlog.",
               "- These numbers describe this file only. They do not prove a trend or explain why complaints happened.",
               ""]
    md_path = output_dir / "complaint_analysis_summary.md"
    md_path.write_text("\n".join(report), encoding="utf-8")

    print(f"Valid complaints: {total}; skipped rows: {skipped}")
    print(f"Saved: {csv_path.name} and {md_path.name}")
    return 0


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("complaints.csv")
    sys.exit(analyze(source))
