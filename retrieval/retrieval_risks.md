# Exercise 2.3.2: Retrieval Risks

The main goal is to get correct answers from the database and policies without letting the assistant make sensitive decisions by itself.

## Main risks and controls

### Text-to-SQL

**Risk:** The assistant could write the wrong query, join the wrong tables, or expose private customer data.

**Controls:**
- Allow `SELECT` queries only, using approved tables and columns.
- Check that the user is allowed to see the requested records.
- Use parameters for IDs and limit large results.
- Check the complaint and account IDs before trusting the result.

### RAG (policy search)

**Risk:** The assistant could use an outdated policy or a section that does not apply.

**Controls:**
- Search only approved documents.
- Filter by active policy, effective date, and access permission.
- Include the policy name, version, and section in the answer.
- If the policy is missing or unclear, say so instead of guessing.

### API and other tools

**Risk:** A tool could update the wrong account, send a message twice, or issue an incorrect refund.

**Controls:**
- Only allow approved actions and check user permissions.
- Verify the exact account or complaint ID.
- Require approval before refunds, account changes, and sensitive messages.
- Check whether an action already happened before running it again.
- Keep a log of the action and its result.

### Automation

**Risk:** One mistake could affect many complaints if the same action runs automatically.

**Controls:**
- Test on a small number of cases first.
- Keep early automation read-only.
- Monitor errors and allow the process to be stopped.
- Require a person to approve bulk or high-impact changes.

## Cases I checked in the data

- **CMP001:** The review decision is `APPROVED`, but the fee is still marked as not reversed. Check whether the refund actually happened before doing anything else.
- **CMP003:** The complaint says there was a duplicate debit, but only one matching account transaction is visible. Do not approve a refund without more evidence.
- **CMP004:** A response says the online banking reset was completed, but the available audit record does not confirm the reset or identity check.
- **CMP009:** The review decision is `ESCALATED`. Do not assume every complaint marked `UNDER_REVIEW` has also been escalated.

## Basic tests

| Test | Expected result |
|---|---|
| Ask for another customer's private records without permission | Block the request |
| Generate `DELETE` or `UPDATE` SQL | Reject it |
| Search for a missing or inactive policy | Say that valid policy evidence is unavailable |
| Try to refund CMP001 a second time | Check the actual payment status and require approval |
| Claim CMP003 has a duplicate debit without a second transaction | Say there is not enough evidence |
| Calculate a business-day deadline without a holiday calendar | Do not give a definite overdue result |
| A refund or message tool times out | Check whether it completed before retrying |

## Limitations

This is a design exercise. No live tools or automation were run. The policy CSV contains short policy sections rather than complete documents. Some account IDs or related records can also be missing, so queries need to handle blank values. A person still needs to review sensitive decisions before any action is taken.
