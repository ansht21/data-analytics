"""Batch ingestion entrypoint: validate -> quarantine/pass -> investigate -> report.

Usage:
  python pipeline/ingest.py --batch fixtures/good_sample.csv
  python pipeline/ingest.py --batch fixtures/bad_nulls.csv --auto-investigate
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import agent_investigate, open_fix_mr, report, trigger
from src.validate import validate_batch


def main() -> int:
    ap = argparse.ArgumentParser(description="Contract-first batch ingestion gate.")
    ap.add_argument("--batch", required=True, help="Raw batch CSV to ingest")
    ap.add_argument("--contract", default=None)
    ap.add_argument("--auto-investigate", action="store_true")
    args = ap.parse_args()

    result = validate_batch(args.batch, args.contract)
    print(result.summary())
    outcome = trigger.handle_result(args.batch, result)
    if outcome.status == "passed":
        print("PASS — batch accepted for cleaning. (Downstream load may proceed.)")
        return 0
    print(f"QUARANTINED -> {outcome.incident_dir}")
    if args.auto_investigate:
        analysis = agent_investigate.analyse(result.to_dict())
        analysis = agent_investigate.enhance_with_llm(analysis, result.to_dict())
        rp = report.write_report(outcome.incident_dir, Path(args.batch).name,
                                 result.to_dict(), analysis)
        mr = open_fix_mr.propose(outcome.incident_dir, Path(args.batch).name,
                                 result.to_dict(), analysis)
        print(f"Report: {rp}\nMR: {json.dumps(mr)}")
    else:
        print("Re-run with --auto-investigate to run the agent + report + fix proposal.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
