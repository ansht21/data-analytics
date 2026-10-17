"""Incident investigator — offline rule-based by default, Groq ReAct when keyed.

Offline analyse(): maps each broken rule to cause, pipeline location,
impact and fix — deterministic, no API key. If GROQ_API_KEY is present
AND langchain libs installed, enhance_with_llm() upgrades the narrative.
"""
from __future__ import annotations

import os
from pathlib import Path

EXPLAIN = {
    "null_customer_id": dict(
        cause="Source system emitted rows with empty _CustomerID (upstream export or join drop).",
        location="pipeline/ingest.py pre-clean gate; cleaning code src/data_cleaning.py drops date-nulls only, so customer-nulls would previously slip to revenue joins.",
        impact="Breaks customer-level revenue attribution; churn/segment joins silently lose these orders.",
        fix="Reject-or-quarantine rule already enforced; add NOT NULL guard in DB schema + upstream export check."),
    "bad_date_format": dict(
        cause="Source switched date serialisation (e.g. ISO YYYY-MM-DD instead of DD/MM/YY slashes).",
        location="src/data_cleaning.py date parsing (pd.to_datetime dayfirst=True) — ISO strings parse but shift day/month semantics.",
        impact="delivery_days / order_to_ship_days miscomputed; SLA + late-rate KPIs corrupt downstream.",
        fix="Normalise all date inputs to ISO at ingestion; add format-allowlist test (this validator)."),
    "non_numeric_money": dict(
        cause="Currency column arrived as free text ('twelve') or new symbol formatting.",
        location="src/data_cleaning.py _clean_money regex — passes through anything matching [$ ,0-9.].",
        impact="revenue/profit become NaN; P&L totals understate.",
        fix="Strict money parser + quarantine on unparseable (enforced); propose upstream numeric export."),
    "chronology_violation": dict(
        cause="Ship/Delivery timestamps out of order — backdated ship scan or timezone bug.",
        location="pipeline/ingest.py business-rule gate R01.",
        impact="Negative delivery_days poison SLA averages and on_time flag.",
        fix="Quarantine + request source resend; add monotonicity test on event log."),
    "duplicate_order": dict(
        cause="Batch re-sent or overlapping extracts (same OrderNumber twice).",
        location="src/data_cleaning.py drop_duplicates covers exact dupes only.",
        impact="Double-counted revenue/profit.",
        fix="Unique(OrderNumber) gate enforced here; dedupe by OrderNumber keeping latest DeliveryDate."),
    "allowed_value": dict(
        cause="New warehouse/channel code appeared that the contract allowlist does not know.",
        location="Contract allowlist in contract/supply_orders.contract.yaml.",
        impact="Segments split; dashboards show 'unknown' buckets.",
        fix="Confirm with ops whether code is legit, then extend allowlist via MR + regression test."),
    "range_violation": dict(
        cause="Out-of-range numeric (negative qty, discount > 1).",
        location="Range checks in this validator.",
        impact="Absurd revenue/profit rows distort aggregates.",
        fix="Clamp-or-quarantine per business sign-off; current policy quarantines."),
    "missing_column": dict(
        cause="Upstream schema change removed/renamed a column.",
        location="Header normalisation in src/validate.py::normalize_headers.",
        impact="Whole batch unloadable; pipeline halts before cleaning.",
        fix="Pin expected schema version; map renamed column in ingest adapter."),
}


def analyse(validation: dict) -> dict:
    findings = []
    for v in validation.get("violations", []):
        rid = v.get("rule_id", "")
        base = None
        for key, info in EXPLAIN.items():
            if rid == key or rid.startswith(key) or rid.startswith("null:") and key == "null_customer_id":
                base = info
                break
        base = base or dict(cause="Unclassified failure — inspect sample rows.",
                            location="Validator gate.", impact="Unknown; batch held.",
                            fix="Review sample rows and extend contract.")
        findings.append({"rule_id": rid, "severity": v.get("severity"),
                         "rows_affected": v.get("rows_affected"), **base})
    worst = "critical" if any(f["severity"] == "critical" for f in findings) else (
        "high" if any(f["severity"] == "high" for f in findings) else "medium")
    return {"severity_overall": worst, "findings": findings,
            "mode": "offline-rule-based"}


def enhance_with_llm(analysis: dict, validation: dict) -> dict:
    """Upgrade narrative via Groq when available; else return analysis unchanged."""
    if not os.getenv("GROQ_API_KEY"):
        analysis["mode"] = "offline-rule-based (no GROQ_API_KEY)"
        return analysis
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage
    except Exception as exc:
        analysis["mode"] = f"offline-rule-based (llm import failed: {exc})"
        return analysis
    try:
        from dotenv import load_dotenv
        load_dotenv()
        llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"), temperature=0)
        prompt = ("You are a data-engineering incident reviewer. Given this validation "
                  f"result {validation} and draft analysis {analysis}, write 3-5 crisp "
                  "sentences: likely root cause, blast radius, and single next fix. "
                  "Ground every claim in the numbers given.")
        out = llm.invoke([HumanMessage(content=prompt)])
        analysis["llm_note"] = str(out.content)[:2000]
        analysis["mode"] = "live-groq-enhanced"
    except Exception as exc:
        analysis["mode"] = f"offline-rule-based (llm call failed: {exc})"
    return analysis


# ---- LangGraph ReAct agent (live mode) + offline fallback ----
# Tools mirror your blueprint: quarantine, pipeline code, git log, warehouse.

REACT_SYSTEM = """You are a data-pipeline incident investigator.
Ground EVERY claim in tool output numbers. Never invent figures.
Produce: what broke, which contract rule, pipeline location,
likely root cause, downstream impact, single recommended fix."""

AGENT_AVAILABLE = False
_agent_err = ""
try:
    from langchain_core.tools import tool as _tool
    from langchain_groq import ChatGroq as _ChatGroq
    from langgraph.prebuilt import create_react_agent as _create
    AGENT_AVAILABLE = True
except Exception as _e:  # offline installs stay green
    _agent_err = f"{type(_e).__name__}: {_e}"

_CTX: dict = {}


def set_context(validation: dict, incident_dir=None) -> None:
    _CTX["validation"] = validation
    _CTX["incident_dir"] = str(incident_dir) if incident_dir else ""


def api_key_present() -> bool:
    try:
        from dotenv import load_dotenv as _load
        _load()
    except Exception:
        pass
    return bool(os.getenv("GROQ_API_KEY"))


def react_available() -> tuple[bool, str]:
    if AGENT_AVAILABLE and api_key_present():
        return True, "live-groq-react"
    if not AGENT_AVAILABLE:
        return False, f"offline (import: {_agent_err})"
    return False, "offline (no GROQ_API_KEY)"


def run_react_agent(user_goal: str = "Investigate this contract breach.") -> dict:
    """Run LangGraph ReAct over quarantine+code+git+warehouse. Offline-safe."""
    ok, mode = react_available()
    if not ok:
        return {"mode": mode, "answer": "",
                "note": "Set GROQ_API_KEY + pip install -r requirements-optional.txt for live ReAct."}
    from dotenv import load_dotenv as _load
    _load()

    @_tool
    def inspect_quarantine() -> str:
        """Sample failing rows + violation details from the validation context."""
        v = _CTX.get("validation", {})
        lines = [f"rows={v.get('total_rows')} rules_broken={len(v.get('violations', []))}"]
        for x in v.get("violations", [])[:6]:
            lines.append(f"- {x['rule_id']} [{x.get('severity')}] {x.get('message')} ({x.get('rows_affected')} rows)")
            for row in (x.get("sample") or [])[:2]:
                lines.append(f"    sample: {row}")
        return "\n".join(lines)

    @_tool
    def read_pipeline_code() -> str:
        """Show the validator gate + upstream cleaning code paths."""
        base = Path(__file__).resolve().parents[1]
        out = []
        for p in [base / "src" / "validate.py",
                  base.parent / "supply-chain-performance-analysis" / "src" / "data_cleaning.py"]:
            try:
                out.append(f"### {p}\n" + p.read_text(encoding="utf-8")[:3000])
            except Exception as e:
                out.append(f"### {p}\n(unreadable: {e})")
        return "\n\n".join(out)[:6000]

    @_tool
    def recent_changes() -> str:
        """Git log of the repo (last 10 commits)."""
        import subprocess
        try:
            r = subprocess.run(["git", "log", "--oneline", "-10"],
                               capture_output=True, text=True, timeout=10,
                               cwd=Path(__file__).resolve().parents[1].parent)
            return r.stdout or "(no git history)"
        except Exception as e:
            return f"(git unavailable: {e})"

    @_tool
    def query_warehouse() -> str:
        """Row/batch counts in warehouse/orders.db for impact sizing."""
        from .warehouse import impact_stats
        return str(impact_stats())

    llm = _ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"), temperature=0)
    agent = _create(model=llm, tools=[inspect_quarantine, read_pipeline_code,
                                      recent_changes, query_warehouse],
                    prompt=REACT_SYSTEM)
    try:
        resp = agent.invoke({"messages": [{"role": "user", "content": user_goal}]})
        return {"mode": "live-groq-react", "answer": str(resp["messages"][-1].content)[:4000]}
    except Exception as exc:
        return {"mode": f"offline (react failed: {exc})", "answer": ""}

