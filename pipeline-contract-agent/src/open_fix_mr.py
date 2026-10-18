"""Fix-proposal + MR automation.

Default (safe): writes fix.patch + mr_body.md into the incident dir for
human review — works with zero credentials. With GITLAB_TOKEN +
GITLAB_PROJECT_ID set, opens a real GitLab MR (else GitHub-style patch).
"""
from __future__ import annotations

import os
from pathlib import Path


def _rule_snippets(rules: list[str]) -> list[str]:
    """Per-rule guardrail proposals — concrete, copy-pasteable."""
    out: list[str] = []
    if any(r.startswith("null") or r == "null_customer_id" for r in rules):
        out += [
            "# GUARD null_customer_id (critical):",
            "# - warehouse DDL: ALTER TABLE orders ALTER COLUMN _CustomerID SET NOT NULL;",
            "# - validator already quarantines empty _CustomerID pre-load.",
            "# - regression: tests/test_regressions.py::test_null_customer_id_quarantined",
        ]
    if any(r.startswith("bad_date_format") for r in rules):
        out += [
            "# GUARD bad_date_format (high):",
            "# - pin source export to DD/MM/YY slashes; reject ISO YYYY-MM-DD at gate.",
            "# - validator: _SLASH_DATE_RE allowlist in src/validate.py (already enforced).",
            "# - regression: tests/test_regressions.py::test_iso_dates_flagged",
        ]
    if any(r.startswith("non_numeric") for r in rules):
        out += [
            "# GUARD non_numeric_money (high):",
            "# - strict money parser parse_money_raw() quarantines unparseable text.",
            "# - propose upstream numeric export (no currency symbols / free text).",
            "# - regression: tests/test_regressions.py::test_text_money_flagged",
        ]
    if any(r.startswith("chronology") for r in rules):
        out += [
            "# GUARD chronology_violation R01 (medium):",
            "# - enforce ProcuredDate <= OrderDate <= ShipDate <= DeliveryDate at gate.",
            "# - monotonicity test on event log; request source resend on violation.",
            "# - regression: tests/test_regressions.py::test_chronology_rule",
        ]
    if any(r.startswith("duplicate") for r in rules):
        out += [
            "# GUARD duplicate_order (medium):",
            "# - Unique(OrderNumber) gate; dedupe keeping latest DeliveryDate.",
            "# - regression: tests/test_regressions.py::test_duplicate_order_quarantined",
        ]
    if any(r.startswith("allowed_value") for r in rules):
        out += [
            "# GUARD allowed_value (high):",
            "# - confirm new code with ops, then extend allowlist in",
            "#   contract/supply_orders.contract.yaml via MR + regression test.",
        ]
    if any(r.startswith("range_violation") for r in rules):
        out += [
            "# GUARD range_violation (medium):",
            "# - policy: quarantine (no silent clamp) pending business sign-off.",
        ]
    if any(r.startswith("missing_column") for r in rules):
        out += [
            "# GUARD missing_column (critical):",
            "# - pin expected schema version; map renamed column in ingest adapter.",
        ]
    if not out:
        out = ["# No specific guards — validator passed or unknown rule."]
    return out


def build_fix_patch(validation: dict) -> str:
    rules = sorted({v["rule_id"] for v in validation.get("violations", [])})
    n_rows = sum(v.get("rows_affected", 0) for v in validation.get("violations", []))
    lines = [
        "--- a/contract/supply_orders.contract.yaml",
        "+++ b/contract/supply_orders.contract.yaml",
        "@@ guardrails added by pipeline-contract-agent @@",
        f"# Auto-proposed guards for broken rules: {', '.join(rules) or 'none'}",
        f"# Rows affected: {n_rows}",
        "# 1. Keep validator as pre-load gate (already enforced).",
        "# 2. Per-rule guardrails proposed:",
        *["# " + s if not s.startswith("#") else s for s in _rule_snippets(rules)],
        "# 3. Add regression test tests/test_regressions.py::test_<rule>.",
        "# HUMAN MUST REVIEW + APPLY — agent proposes only.",
    ]
    return "\n".join(lines) + "\n"


def mr_body(batch_name: str, validation: dict, analysis: dict) -> str:
    lines = [f"## Contract breach: `{batch_name}`",
             f"Severity: {analysis.get('severity_overall')} | Mode: {analysis.get('mode')}", ""]
    for v in validation.get("violations", []):
        lines.append(f"- {v['rule_id']}: {v['message']} ({v['rows_affected']} rows)")
    lines += ["", "Quarantined, cleaned data untouched. See incident_report.md."]
    return "\n".join(lines)


def propose(incident_dir: str | Path, batch_name: str, validation: dict, analysis: dict) -> dict:
    incident_dir = Path(incident_dir)
    (incident_dir / "fix.patch").write_text(build_fix_patch(validation), encoding="utf-8")
    (incident_dir / "mr_body.md").write_text(mr_body(batch_name, validation, analysis), encoding="utf-8")
    token, pid = os.getenv("GITLAB_TOKEN"), os.getenv("GITLAB_PROJECT_ID")
    if not (token and pid):
        return {"mr": "dry-run", "detail": "Set GITLAB_TOKEN + GITLAB_PROJECT_ID to open a live MR. fix.patch ready."}
    try:
        import gitlab
        from dotenv import load_dotenv
        load_dotenv()
        gl = gitlab.Gitlab(os.getenv("GITLAB_API_URL", "https://gitlab.com"), private_token=token)
        proj = gl.projects.get(pid)
        mr = proj.mergerequests.create({
            "source_branch": f"fix/contract-{incident_dir.name[:16]}",
            "target_branch": os.getenv("GITLAB_TARGET_BRANCH", "main"),
            "title": f"fix(data-contract): quarantine + guard {batch_name}",
            "description": mr_body(batch_name, validation, analysis),
        })
        return {"mr": "opened", "url": mr.web_url}
    except Exception as exc:
        return {"mr": "failed", "detail": f"{type(exc).__name__}: {exc}. fix.patch retained."}
