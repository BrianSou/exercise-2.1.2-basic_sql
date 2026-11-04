"""Build both local databases and refresh the exercise reports."""
import argparse
import subprocess
import sys
from pathlib import Path
from legacy.build_database import seed
from legacy.generate_evidence import run as generate_evidence
from legacy.build_data_dictionary import build as build_data_dictionary
from analysis.complaint_analysis import analyze

ROOT=Path(__file__).resolve().parent

def run(reset=False):
    original=ROOT/'data/original.db'
    bulk=ROOT/'data/bulk.db'
    if reset or not original.exists():
        counts=seed(original,reset=reset)
        print('Loaded original dataset:',counts['complaint'],'complaints')
    else:
        print('Original database exists. Not replacing it.')
    generate_evidence(original)
    build_data_dictionary(original)
    if reset or not bulk.exists():
        args=[sys.executable,str(ROOT/'bulk/seed_database.py'),'--data-dir',str(ROOT/'bulk/data'),'--db',str(bulk)]
        if reset: args.append('--reset')
        result=subprocess.run(args,cwd=ROOT)
        if result.returncode:
            raise RuntimeError('Bulk database seed failed. See bulk/data/seed_run_log.txt.')
    else:
        print('Bulk database exists. Not replacing it.')
    if analyze(ROOT/'bulk/data/complaints.csv',ROOT/'bulk/outputs'):
        raise RuntimeError('Complaint CSV analysis failed')
    for name in ('seed_run_log.txt','integrity_report.txt','rejected_rows.csv'):
        source=ROOT/'bulk/data'/name
        if source.exists():
            (ROOT/'bulk/outputs'/name).write_bytes(source.read_bytes())
    print('Setup finished.')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--reset',action='store_true',help='Recreate both databases from the CSVs')
    run(reset=p.parse_args().reset)
