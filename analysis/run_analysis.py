"""Run the 120-complaint CSV analysis."""
from pathlib import Path
from complaint_analysis import analyze
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    raise SystemExit(analyze(ROOT/'bulk/data/complaints.csv',ROOT/'bulk/outputs'))
