"""Export the original SQL results and simple checks."""
from pathlib import Path
import sqlite3
import csv
import json
from datetime import date

HERE=Path(__file__).resolve().parent

def save_csv(path, headers, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)

def run(db_path):
    out=HERE/'outputs'
    docs=HERE/'docs'
    out.mkdir(exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.row_factory=sqlite3.Row
        number=lambda query: db.execute(query).fetchone()[0]
        total=number('SELECT COUNT(*) FROM complaint')
        joined=number('SELECT COUNT(*) FROM complaint_analyst_view')
        distinct_joined=number('SELECT COUNT(DISTINCT complaint_id) FROM complaint_analyst_view')
        missing_account=number('SELECT COUNT(*) FROM complaint WHERE account_id IS NULL')
        fk_errors=len(db.execute('PRAGMA foreign_key_check').fetchall())
        counts={t:number('SELECT COUNT(*) FROM '+t) for t in ('customer','account','complaint','service_request','complaint_status_history','review_request','review_decision')}
        owner_mismatch=number('SELECT COUNT(*) FROM complaint c JOIN account a ON a.account_id=c.account_id WHERE c.customer_id<>a.customer_id')
        if total != joined or joined != distinct_joined or fk_errors or owner_mismatch:
            raise ValueError('Original database integrity checks did not pass')
        (out/'seed_validation.txt').write_text('ORIGINAL DATABASE\n'+'\n'.join(f'{k}: {v}' for k,v in counts.items()) + f'\nForeign key errors: {fk_errors}\nWrong account owner: {owner_mismatch}\nResult: PASS\n',encoding='utf-8')
        basics=[]
        queries={
            'open': "SELECT complaint_id,status FROM complaint WHERE status='OPEN' ORDER BY complaint_id",
            'high_unresolved': "SELECT complaint_id,status FROM complaint WHERE priority='High' AND status<>'CLOSED' ORDER BY complaint_id",
            'recent': 'SELECT complaint_id,status FROM complaint ORDER BY received_at DESC LIMIT 10',
        }
        for name,sql in queries.items():
            basics += [(name,r[0],r[1]) for r in db.execute(sql)]
        save_csv(out/'basic_query_results.csv',['query','complaint_id','status'],basics)
        notes=['# Database exploration','']
        for table in counts:
            empties=[]
            for column in db.execute('PRAGMA table_info('+table+')'):
                col=column['name']
                ct=number('SELECT COUNT(*) FROM '+table+' WHERE "'+col+'" IS NULL')
                if ct: empties.append(f'{col}: {ct}')
            notes.append(f'- {table}: {counts[table]} rows; missing values: '+(', '.join(empties) if empties else 'none'))
        (docs/'query_exploration.md').write_text('\n'.join(notes)+'\n',encoding='utf-8')
        (docs/'query_notes.md').write_text("# Query notes\n\n- `status = 'OPEN'` only shows complaints currently open.\n- Filter dates using `>=` for the start and `<` for the day after the end.\n- `LEFT JOIN account` keeps complaints that have no account ID.\n- SQLite uses `strftime` and `julianday` for dates.\n- Complaint closure dates are not in the original `complaint` table.\n",encoding='utf-8')
        (docs/'join_validation.md').write_text(f'# Join check\n\nOriginal rows: {total}\n\nRows after joins: {joined}\n\nDistinct complaints after joins: {distinct_joined}\n\nMissing account IDs: {missing_account}\n\nNo complaint rows were lost or duplicated.\n',encoding='utf-8')
        no_account=[r[0] for r in db.execute('SELECT complaint_id FROM complaint_analyst_view WHERE account_id IS NULL ORDER BY complaint_id')]
        (docs/'missing_account_test.md').write_text('# Missing-account test\n\n`SELECT complaint_id FROM complaint_analyst_view WHERE account_id IS NULL;`\n\nRows kept: '+str(len(no_account))+'\n\nIDs: '+', '.join(no_account)+'\n',encoding='utf-8')
        metrics=[]
        for group,count in db.execute('SELECT status,COUNT(*) FROM complaint GROUP BY status ORDER BY status'): metrics.append(('status_count',group,count))
        for group,count in db.execute('SELECT category,COUNT(*) FROM complaint GROUP BY category ORDER BY category'): metrics.append(('category_count',group,count))
        for group,count in db.execute("SELECT strftime('%Y-%m',received_at),COUNT(*) FROM complaint GROUP BY 1 ORDER BY 1"): metrics.append(('received_month_count',group,count))
        metrics.extend([
            ('total_complaints','',total),
            ('open_backlog','',number("SELECT COUNT(*) FROM complaint WHERE status<>'CLOSED'")),
            ('distinct_customers','',number('SELECT COUNT(DISTINCT customer_id) FROM complaint')),
            ('escalated_unresolved','',number("SELECT COUNT(DISTINCT rr.complaint_id) FROM review_request rr JOIN review_decision rd ON rd.review_request_id=rr.review_request_id JOIN complaint c ON c.complaint_id=rr.complaint_id WHERE rd.decision='ESCALATED' AND c.status<>'CLOSED'")),
            ('avg_resolution_days','all categories','N/A: no reliable closure date')
        ])
        save_csv(out/'complaint_metrics.csv',['metric','group','value','as_of_date'],[(*row,date.today().isoformat()) for row in metrics])
        sql=(HERE/'sql/advanced_queries.sql').read_text(encoding='utf-8')
        sql='\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--'))
        results=[]
        for index,statement in enumerate((part.strip() for part in sql.split(';') if part.strip()),1):
            cur=db.execute(statement)
            fields=[col[0] for col in cur.description]
            for row in cur: results.append((index,json.dumps(dict(zip(fields,row))),date.today().isoformat()))
        save_csv(out/'advanced_query_results.csv',['query_number','row_json','as_of_date'],results)
        (docs/'advanced_sql_explanation.md').write_text('# Advanced SQL notes\n\n- `CASE` groups unresolved complaints by 0-7, 8-30, and 31+ days.\n- CTEs break repeat-customer and escalation logic into named steps.\n- `ROW_NUMBER()` finds the latest status using timestamp and history ID.\n- `PARTITION BY complaint_id` restarts numbering for each complaint.\n- `RANK()` gives tied complaint counts the same rank.\n- `LEFT JOIN` keeps cases with no history record.\n- Aging results depend on the date the query runs.\n',encoding='utf-8')
        print(f'Original: {total} complaints; {joined} analyst rows; {fk_errors} FK errors')

if __name__=='__main__':
    run(HERE.parent/'data/original.db')
