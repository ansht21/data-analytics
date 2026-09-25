"""Deterministic executive brief: KPIs + top risks + recommended decisions + chart picks.

Runs 100% offline on the loaded DataFrame. The Streamlit app renders this with
KPI cards, Plotly charts and a Markdown download button.
"""
from __future__ import annotations

import pandas as pd

from .analytics import CHIPS, run_chip
from .datasets import dataset_kpis

BRIEF_INTROS = {
    "supply": (
        "Half of all orders miss the 5-day delivery target, with $36.3M of net revenue "
        "exposed. The question for leadership: fix a warehouse, or fix the network?"
    ),
    "uber": (
        "Demand concentrates violently in the evening peak while airport trips carry "
        "the revenue. The question: when to surge, where to position premium cars, "
        "which tier to grow?"
    ),
    "churn": (
        "More than one in four customers churns, and the revenue at risk concentrates "
        "in one cohort. The question: who to save first, and with what offer?"
    ),
}

RISKS = {
    "supply": [
        ("Margin bleed from deep discounts", "20%+ discount orders realise a fraction of normal margin."),
        ("Network-wide late delivery", "Late rate sits near 50%; blaming one warehouse misfires."),
        ("Tail-SKU complexity", "Dozens of tail SKUs add cost for ~20% of revenue."),
    ],
    "uber": [
        ("Surge mistiming", "Acting on the volume peak is an hour too late."),
        ("Airport-supply fragility", "Over half the revenue rides on ~40% of trips."),
        ("Low-yield volume tiers", "Pool/X dilute per-km yield vs premium tiers."),
    ],
    "churn": [
        ("Month-to-month fiber concentration", "One cohort holds the bulk of revenue at risk."),
        ("First-year onboarding cliff", "New customers churn many times faster than veterans."),
        ("Billing-friction exits", "Manual payment methods correlate with the highest churn."),
    ],
}

DECISIONS = {
    "supply": [
        "Apply product-level profit floors; route every 20%+ discount through approval.",
        "Fix upstream scheduling network-wide — do NOT fund a per-site warehouse programme.",
        "Ring-fence A-item stock; review tail SKUs for delisting or made-to-order.",
    ],
    "uber": [
        "Launch driver incentives by 4:30 PM, an hour ahead of the volume peak.",
        "Protect airport-corridor supply with a dedicated queue and reliability bonuses.",
        "Grow the premium fleet first; keep Pool/X as feeder volume.",
    ],
    "churn": [
        "Offer month-to-month fiber users a 1-year loyalty contract; prioritise saves by dollars at risk.",
        "Fund a 90-day onboarding programme (check-ins, first-bill clarity).",
        "Nudge electronic-check users to autopay with a small bill credit.",
    ],
}


def build_brief(key: str, df: pd.DataFrame) -> dict:
    """Assemble the brief dict: intros, KPIs, chip insights, risks, decisions, markdown."""
    kpis = dataset_kpis(key, df)
    insights = [run_chip(key, label, df) for label, _ in CHIPS[key]]
    return {"key": key, "intro": BRIEF_INTROS[key], "kpis": kpis,
            "insights": insights, "risks": RISKS[key], "decisions": DECISIONS[key]}


def brief_markdown(brief: dict, dataset_label: str) -> str:
    lines = [f"# Executive Brief — {dataset_label}", "", brief["intro"], "",
             "## Topline KPIs", ""]
    for label, value in brief["kpis"]:
        lines.append(f"- **{label}:** {value}")
    lines += ["", "## Key findings", ""]
    for i, ins in enumerate(brief["insights"], 1):
        lines += [f"### {i}. {ins.finding}", "", f"- *Why it matters:* {ins.explanation}",
                  f"- *Recommended decision:* {ins.suggestion}", ""]
    lines += ["## Top risks", ""]
    lines += [f"- **{t}:** {d}" for t, d in brief["risks"]]
    lines += ["", "## Recommended decisions", ""]
    lines += [f"{i}. {d}" for i, d in enumerate(brief["decisions"], 1)]
    lines += ["", "_Generated offline by the Business Intelligence AI Agent — every figure "
                   "computed live with pandas; inspect-query expanders in the app show the code._"]
    return "\n".join(lines)
