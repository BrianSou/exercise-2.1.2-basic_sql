# Advanced SQL Explanation

I used SQLite to look at complaint ages, repeat customers, status history, and customer rankings. The results below are from the data I tested on October 23, 2026.

## 1. Age buckets

I used `CASE` to group unresolved complaints by how long they've been open. The age is the number of calendar days between `received_at` and today's date. I left out closed complaints and missing or future dates.

I tested the boundaries: 7 days went into **0–7**, 8 and 30 went into **8–30**, and 31 went into **31+**.

**Results:** 1 complaint was 0–7 days old, 0 were 8–30 days old, and 9 were 31+ days old. The query returns one row per bucket, including buckets with zero complaints.

**Limitation:** The counts change each day. I also assumed `CLOSED` is the only resolved status.

## 2. Repeat complainants (CTEs)

I used `repeat_complainants` to count complaints per customer and keep customers with more than one. I used `escalation_context` to check whether any of their complaints had an `ESCALATED` review decision. Joining the two results shows the complaints for each repeat customer.

**Result:** `CUS001` was the only repeat customer, with 2 complaints (`CMP001` and `CMP011`). Neither had a recorded escalation. The query gives one row per complaint made by a repeat customer.

**Limitation:** An escalation decision only shows that a complaint was escalated at some point, not that it's still escalated.

## 3. Latest complaint status (ROW_NUMBER)

I used `ROW_NUMBER()` to find the latest status-history entry for each complaint.

- `PARTITION BY complaint_id` starts the numbering over for each complaint.
- `ORDER BY changed_at DESC` puts the newest change first.
- `history_id DESC` breaks ties when two changes have the same time.
- Keeping row 1 gives the latest recorded status.

**Result:** The query returns one row per complaint (11 rows). `CMP011` has no status-history entry, so those fields are blank.

**Limitation:** This only works with the status changes that were actually recorded.

## 4. Rank customers by complaint count

I counted each customer's complaints, then used `RANK()` to put customers with the most complaints first. Customers with the same count get the same rank. I used `ROW_NUMBER()` with `customer_id` to keep the display order consistent when counts are tied.

**Result:** `CUS001` ranked 1st with 2 complaints. The other 9 customers each had 1 complaint and tied for 2nd. The query returns one row per customer.

**Limitation:** Tied customers share a rank, even though they appear on separate rows.

## Checks

I checked that the age buckets add up to **10 unresolved complaints**. The latest-status query returns **11 rows**, matching the 11 complaints. The ranking returns **10 rows**, matching the 10 distinct customers. The age-boundary tests also returned the expected buckets.
