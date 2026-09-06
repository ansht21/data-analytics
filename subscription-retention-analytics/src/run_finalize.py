"""
run_finalize.py
---------------
Lean second pass: reuses the already-written ML outputs and only produces the
SHAP artifacts, revenue-at-risk, saved models, and the GenAI Copilot
evaluation. Avoids recomputing the slow cross-validation.

    python src/run_finalize.py            # offline (template Copilot)
    python src/run_finalize.py --live     # use Groq/OpenAI key from .env
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_processing import load_and_clean, add_tenure_band
import modeling as mdl
from feature_engineering import build_features
import explainability as exp
from genai import LLMProvider
import evaluation as ev

FINAL_NAME = "Random Forest"


def main(live: bool) -> None:
    df = add_tenure_band(load_and_clean())
    out, mdir = ROOT / "outputs", ROOT / "models"
    mdir.mkdir(parents=True, exist_ok=True)

    sp = mdl.make_splits(df)
    rf = mdl.fit_models(sp)["Random Forest"]
    prob_test = rf.predict_proba(sp["X_test"])[:, 1]
    thr = json.loads((out / "threshold.json").read_text())
    FINAL_THRESHOLD = thr["cost_optimal"]

    # full-data scores + revenue (refit scaler on full features)
    feats = build_features(df)
    scaler = StandardScaler().fit(feats)
    df_out = df.copy()
    df_out["churn_probability"] = rf.predict_proba(feats)[:, 1]
    df_out["risk_level"] = df_out["churn_probability"].map(mdl.risk_band)
    df_out.to_csv(out / "churn_predictions_all.csv", index=False)

    explainer = exp.get_explainer(rf, feats.head(200), FINAL_NAME)
    global_imp = exp.global_importance(explainer, feats.head(400), top_n=12)
    global_imp.to_csv(out / "shap_global_importance.csv", index=False)

    rav = mdl.revenue_at_risk(df_out)
    (out / "revenue_at_risk.json").write_text(json.dumps(
        {k: (v if not isinstance(v, pd.Series) else v.head(5).to_dict())
         for k, v in rav.items()}, indent=2, default=str))

    for f, obj in [("final_model.pkl", rf), ("explainer.pkl", explainer),
                   ("scaler_full.pkl", scaler)]:
        with open(mdir / f, "wb") as fh:
            pickle.dump(obj, fh)
    (mdir / "meta.json").write_text(json.dumps(
        {"final_model": FINAL_NAME, "threshold": FINAL_THRESHOLD,
         "high_risk": mdl.HIGH_RISK, "medium_risk": mdl.MEDIUM_RISK}, indent=2))

    # GenAI evaluation
    cases = ev.build_eval_cases(sp, df, prob_test, n=30)
    provider = LLMProvider() if live else LLMProvider(api_key="")
    results = ev.run_evaluation(cases, df, rf, explainer, scaler, FINAL_NAME, provider)
    results.to_csv(out / "genai_evaluation_results.csv", index=False)
    summary = ev.summarize_evaluation(results)
    summary.to_csv(out / "genai_evaluation_summary.csv", index=False)
    neg = ev.run_negative_tests(provider)
    neg.to_csv(out / "genai_negative_tests.csv", index=False)

    # report
    print("\n=== GLOBAL SHAP (top 10) ===")
    print(global_imp.head(10).to_string(index=False))
    print("\n=== LOCAL SHAP example (highest-risk customer) ===")
    best = df_out.sort_values("churn_probability", ascending=False).iloc[0]
    rec = exp.build_customer_risk_record(df, best.customerID, rf, explainer, scaler, FINAL_NAME)
    print(json.dumps(rec, indent=2))
    print("\n=== REVENUE AT RISK ===")
    print(f"  flagged: {rav['flagged_customers']} | "
          f"expected monthly $ at risk: {rav['expected_monthly_revenue_at_risk']} | "
          f"gross exposure: {rav['gross_monthly_exposure_flagged']}")
    print("\n=== GENAI EVALUATION (one representative case) ===")
    print(json.dumps(results.iloc[-5].to_dict(), indent=2))
    print("\n=== GENAI EVALUATION SUMMARY ===")
    print(summary.to_string(index=False))
    print("\n=== NEGATIVE GROUNDING TESTS ===")
    print(neg.to_string(index=False))
    print("\nWrote models/ + outputs/ (shap, revenue, genai).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    main(live=args.live)