"""Incident report writer: validation + analysis -> incident_report.md."""
from __future__ import annotations

from pathlib import Path


def write_report(incident_dir: str | Path, batch_name: str, validation: dict, analysis: dict) -> Path:
    incident_dir = Path(incident_dir)
    lines = [f"# Incident Report — `{batch_name}`", "",
             f"**Overall severity:** {analysis.get('severity_overall', '?')}  ",
             f"**Mode:** {analysis.get('mode', 'offline')}  ",
             f"**Rows scanned:** {validation.get('total_rows', '?')}  ",
             f"**Rules broken:** {len(validation.get('violations', []))}", "",
             "## What broke", ""]
    for v in validation.get("violations", []):
        lines += [f"- **{v['rule_id']}** [{v.get('severity')}] — {v.get('message')} "
                  f"({v.get('rows_affected')} rows)"]
    lines += ["", "## Root cause -> impact -> fix", ""]
    for i, f in enumerate(analysis.get("findings", []), 1):
        lines += [f"### {i}. {f['rule_id']} [{f.get('severity')}]",
                  f"- **Likely cause:** {f.get('cause')}",
                  f"- **Pipeline location:** `{f.get('location')}`",
                  f"- **Downstream impact:** {f.get('impact')}",
                  f"- **Suggested fix:** {f.get('fix')}", ""]
    if analysis.get("llm_note"):
        lines += ["## LLM reviewer note", "", analysis["llm_note"], ""]
    if analysis.get("react_answer"):
        lines += ["## ReAct agent investigation", "", analysis["react_answer"], ""]
    lines += ["## Audit trail",
              "- `batch__*` — quarantined offending batch (untouched)",
              "- `validation.json` — deterministic validator output",
              "- `manifest.json` — quarantine receipt",
              "- `incident_report.md` — this file (rule -> root cause -> impact)",
              "- `fix.patch` — proposed guardrail/test (human must approve + apply)", ""]
    out = incident_dir / "incident_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
