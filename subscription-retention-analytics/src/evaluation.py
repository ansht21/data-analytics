"""
evaluation.py
-------------
Real evaluation harness for the GenAI Retention Copilot.

Test cases are generated from ACTUAL project data (stratified sample of the
held-out customers). The same cases are run against all three prompt
versions. Metrics reported (measured, never invented):

  * schema validity          — JSON parsed + all required fields present
  * grounding/driver agreement — top_drivers in the response match the
                                 model-supported SHAP drivers supplied
  * probability fidelity     — reported churn_probability matches the model's
  * unsupported claims       — regex scan for complaint/satisfaction/
                               competitor/policy claims (must be zero)
  * recommendation separation— retention considerations must be present
  * completeness             — missing_information + limitations acknowledged

Negative test cases: payloads with unavailable fields requested are checked
to ensure the model answers with the required unavailable-information phrase
rather than inventing facts.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd

from genai import (LLMProvider, REQUIRED_PHRASE, PROMPTS,
                   generate_copilot_response, check_unsupported_claims,
                   scan_claims)

N_CASES = 30  # adjust if API budget/time is tight


def build_eval_cases(sp: dict, df: pd.DataFrame, prob_test,
                     n: int = N_CASES) -> list[dict]:
    """Stratified sample of held-out customers: mix of churned/retained and
    High/Medium/Low risk bands, chosen deterministically."""
    from modeling import risk_band
    idx = list(sp["X_test"].index)
    base = pd.DataFrame({
        "customerID": df.loc[idx, "customerID"].values,
        "actual": np.asarray(sp["y_test"]),
        "band": [risk_band(float(p)) for p in prob_test],
    })
    per = max(1, n // 6)
    picked = []
    for key, grp in base.groupby(["actual", "band"]):
        picked.append(grp.head(per))
    cases = pd.concat(picked, ignore_index=True).head(n).reset_index(drop=True)
    return [{"customerID": str(r["customerID"]), "actual": int(r["actual"]),
             "band": str(r["band"])} for _, r in cases.iterrows()]


def evaluate_case(case: dict, df: pd.DataFrame, model, explainer, scaler,
                  model_name: str, provider: LLMProvider | None = None,
                  prompt_version: str = "C_structured") -> dict:
    """Run one eval case through the Copilot and score the response."""
    from explainability import build_customer_risk_record
    rec = build_customer_risk_record(df, case["customerID"], model,
                                     explainer, scaler, model_name)
    resp = generate_copilot_response(rec, prompt_version, provider)
    val = resp.get("validation", {})
    scores = {
        "customerID": case["customerID"], "prompt_version": prompt_version,
        "actual_churn": case["actual"], "band": case["band"],
        "schema_valid": bool(val.get("schema_valid")),
        "unsupported_claims": len(val.get("unsupported_claims", [])),
    }
    if scores["schema_valid"]:
        scores["driver_agreement"] = _driver_agreement(rec, resp)
        scores["prob_fidelity"] = abs(float(resp["churn_probability"])
                                      - rec["churn_probability"]) < 0.01
        scores["reco_separated"] = len(resp.get("retention_considerations", [])) > 0
        scores["acknowledges_missing"] = len(resp.get("missing_information", [])) > 0
        scores["acknowledges_limitations"] = len(resp.get("limitations", [])) > 0
    else:
        for k in ("driver_agreement", "prob_fidelity", "reco_separated",
                  "acknowledges_missing", "acknowledges_limitations"):
            scores[k] = False
        scores["error"] = val.get("error", "unknown")
    return scores


def _driver_agreement(record: dict, resp: dict) -> bool:
    """Response top_drivers must overlap the supplied model-supported drivers."""
    supplied = {d.lower().split("_")[0] for d in record["top_drivers"]}
    claimed = {str(d).lower().split("_")[0] for d in resp.get("top_drivers", [])}
    return bool(supplied & claimed)


def run_evaluation(cases: list[dict], df: pd.DataFrame, model, explainer,
                   scaler, model_name: str, provider: LLMProvider | None = None,
                   prompt_versions: list[str] | None = None) -> pd.DataFrame:
    """Run all cases x all prompt versions; identical cases per version."""
    rows = []
    for version in (prompt_versions or list(PROMPTS)):
        for case in cases:
            rows.append(evaluate_case(case, df, model, explainer, scaler,
                                      model_name, provider, version))
    return pd.DataFrame(rows)


def summarize_evaluation(results: pd.DataFrame) -> pd.DataFrame:
    """Measured pass rates per prompt version — no fabricated numbers."""
    g = results.groupby("prompt_version")
    out = pd.DataFrame({
        "cases": g.size(),
        "schema_valid_rate": g.schema_valid.mean().round(3),
        "driver_agreement_rate": g.driver_agreement.mean().round(3),
        "prob_fidelity_rate": g.prob_fidelity.mean().round(3),
        "unsupported_claims_per_case": g.unsupported_claims.mean().round(3),
        "reco_separated_rate": g.reco_separated.mean().round(3),
        "missing_ack_rate": g.acknowledges_missing.mean().round(3),
        "limitations_ack_rate": g.acknowledges_limitations.mean().round(3),
    })
    return out.reset_index()


def negative_grounding_cases() -> list[dict]:
    """
    Explicit negative tests: the analyst asks about data the dataset does
    NOT contain. A grounded system must answer with the required phrase
    (live LLM) or list the field under missing_information (offline mode).
    """
    return [
        {"question": "What complaints has this customer made recently?",
         "expect_unavailable": True},
        {"question": "How satisfied is this customer with support?",
         "expect_unavailable": True},
        {"question": "Has a competitor offered them a better deal?",
         "expect_unavailable": True},
        {"question": "How many support tickets did they open last month?",
         "expect_unavailable": True},
    ]


def run_negative_tests(provider: LLMProvider | None = None) -> pd.DataFrame:
    """Check the grounding instructions hold on out-of-domain questions."""
    from genai import SYSTEM_GROUNDING_RULES
    provider = provider or LLMProvider()
    rows = []
    for case in negative_grounding_cases():
        user = (f"Customer payload: {{\"customerID\": \"0001\", "
                f"\"Contract\": \"Month-to-month\", \"tenure\": 5, "
                f"\"churn_probability\": 0.87, \"risk_level\": \"High\"}}\n\n"
                f"Analyst question: {case['question']}\n"
                f"If the payload lacks the answer, respond with a JSON object "
                f"containing \"missing_information\" listing the unavailable "
                f"data and use exactly: {REQUIRED_PHRASE}")
        raw = provider.chat(SYSTEM_GROUNDING_RULES, user)
        try:  # scan only claim-bearing sections when the reply is valid JSON
            parsed = json.loads(raw)
            claims = scan_claims(parsed) if isinstance(parsed, dict) \
                else check_unsupported_claims(raw)
        except json.JSONDecodeError:
            claims = check_unsupported_claims(raw)
        rows.append({
            "question": case["question"],
            "answered_unavailable": REQUIRED_PHRASE.lower() in raw.lower()
                                    or "missing_information" in raw,
            "unsupported_claims": claims,
            "grounded": not claims,
        })
    return pd.DataFrame(rows)
