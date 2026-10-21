"""Orchestrator: ingest -> validate -> PASS load | FAIL quarantine+agent.

Single entrypoint for CLI, API and scheduler:
  python -m src.pipeline --batch <csv> [--auto-investigate]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import agent_investigate, open_fix_mr, report, trigger, warehouse
from src.contract import contract_info
from src.paths import CONTRACT_PATH
from src.validate import validate_batch


def run(batch: str | Path, auto_investigate: bool = True) -> dict:
    batch = Path(batch)
    info = contract_info(CONTRACT_PATH)
    result = validate_batch(batch)
    if result.passed:
        loaded = warehouse.load_to_warehouse(batch)
        return {"status": "passed", "contract": info,
                "validation": result.to_dict(), "warehouse": loaded}
    outcome = trigger.handle_result(batch, result)
    payload: dict = {"status": "quarantined", "contract": info,
                     "validation": result.to_dict(),
                     "incident_dir": str(outcome.incident_dir)}
    if auto_investigate:
        agent_investigate.set_context(result.to_dict(), outcome.incident_dir)
        analysis = agent_investigate.enhance_with_llm(
            agent_investigate.analyse(result.to_dict()), result.to_dict())
        react = agent_investigate.run_react_agent(
            f"Investigate contract breach in batch {batch.name}: "
            f"{len(result.violations)} rule(s) broken.")
        if react.get("answer"):
            analysis["react_answer"] = react["answer"]
            analysis["mode"] = react["mode"]
        rp = report.write_report(outcome.incident_dir, batch.name,
                                 result.to_dict(), analysis)
        mr = open_fix_mr.propose(outcome.incident_dir, batch.name,
                                 result.to_dict(), analysis)
        payload.update({"analysis": analysis, "report": str(rp), "mr": mr})
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Contract-first pipeline run.")
    ap.add_argument("--batch", required=True)
    ap.add_argument("--auto-investigate", action="store_true", default=True)
    ap.add_argument("--no-investigate", action="store_true")
    args = ap.parse_args()
    out = run(args.batch, auto_investigate=not args.no_investigate)
    print(f"{out['status'].upper()}: {args.batch}")
    for v in out["validation"]["violations"]:
        print(f"  - [{v['severity']}] {v['rule_id']}: {v['message']} ({v['rows_affected']} rows)")
    if out["status"] == "passed":
        print(f"Loaded -> {out['warehouse']}")
    else:
        print(f"Incident -> {out.get('incident_dir')}")
    return 0 if out["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
