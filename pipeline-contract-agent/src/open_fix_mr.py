"""Fix-proposal + MR automation.

Default (safe): writes fix.patch + mr_body.md into the incident dir for
human review — works with zero credentials. With GITLAB_TOKEN +
GITLAB_PROJECT_ID set, opens a real GitLab MR (else GitHub-style patch).
"""
from __future__ import annotations

import os
from pathlib import Path


def build_fix_patch(validation: dict) -> str:
    rules = sorted({v["rule_id"] for v in validation.get("violations", [])})
    return (
        "--- a/contract/supply_orders.contract.yaml\n"
        "+++ b/contract/supply_orders.contract.yaml\n"
        "@@ guardrails added by pipeline-contract-agent @@\n"
        f"# Auto-proposed guards for broken rules: {', '.join(rules) or 'none'}\n"
        "# 1. Keep validator as pre-load gate (already enforced).\n"
        "# 2. Add NOT NULL constraint on _CustomerID in warehouse DDL.\n"
        "# 3. Pin date serialisation to DD/MM/YY at source export.\n"
        "# 4. Add regression test tests/test_regressions.py::test_<rule>.\n"
    )


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
