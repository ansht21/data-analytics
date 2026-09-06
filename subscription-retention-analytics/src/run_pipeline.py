"""
run_pipeline.py
---------------
End-to-end orchestration for Subscription Retention Intelligence.

Runs: load -> splits -> models -> CV -> threshold/calibration/error analysis
-> SHAP -> revenue-at-risk -> evaluate Copilot prompts -> writes all results
to outputs/ and models/ so the Streamlit app and notebooks can reuse them.

Usage:
    python src/run_pipeline.py            # offline; no API key required
    python src/run_pipeline.py --live     # also calls the Groq/OpenAI API
"""
from __future__ import annotations

import argparse
import json
import os
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


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def stage_ml(df: pd.DataFrame):
    """Splits, models, CV, threshold, calibration, error analysis, SHAP,
    revenue-at-risk. Returns a context dict reused by the GenAI stage."""
    out = ensure_dir(ROOT / "outputs")
    mdir = ensure_dir(ROOT / "models")
    os.makedirs(ROOT / "image", exist_ok=True)

    sp = mdl.make_splits(df)
    models = mdl.fit_models(sp)
    rf = models["Random Forest"]

    cv = mdl.cross_validate(sp)
    cv.to_csv(out / "churn_cross_validation.csv", index=False)

    evals = {
        "Logistic Regression": mdl.evaluate_model("Logistic Regression", models["Logistic Regression"], sp["X_test_s"], sp["y_test"]),
        "Random Forest": mdl.evaluate_model("Random Forest", rf, sp["X_test"], sp["y_test"]),
    }
    rows = []
    for name, e in evals.items():
        rows.append({"model": name, "accuracy": e["accuracy"],
                     "precision": e["precision"], "recall": e["recall"],
                     "f1": e["f1"], "roc_auc": e["roc_auc"],
                     "pr_auc": e["pr_auc"], "brier": e["brier"],
                     "threshold": e["threshold"]})
    metrics_df = (pd.DataFrame(rows).round(4)[
        ["model", "accuracy", "precision", "recall", "f1",
         "roc_auc", "pr_auc", "brier", "threshold"]])
    metrics_df.to_csv(out / "churn_model_metrics.csv", index=False)

    # FINAL model: Random Forest. Rationale (measured): held-out ROC-AUC and
    # PR-AUC are statistically tied with Logistic Regression (CV means
    # 0.8456±0.0056 vs 0.8497±0.0042 — overlapping within noise; LogReg edges
    # held-out AUC by ~0.001). RF is deployed because it captures non-linear
    # interactions without scaling and supports exact, fast TreeSHAP local
    # attributions for the per-customer explanations the Copilot requires.
    final_name = "Random Forest"
    final_model = rf
    prob_test = final_model.predict_proba(sp["X_test"])[:, 1]
    thr = mdl.optimize_threshold(sp["y_test"].values, prob_test)
    FINAL_THRESHOLD = thr["cost_optimal"]
    (out / "threshold.json").write_text(json.dumps(thr, indent=2))

    cal = mdl.calibration_table(sp["y_test"].values, prob_test)
    cal.to_csv(out / "churn_calibration.csv", index=False)

    err = mdl.error_analysis(sp["y_test"].values, prob_test, sp["X_test"], df, FINAL_THRESHOLD)
    (out / "error_analysis.json").write_text(json.dumps(err, indent=2))

    # full-data scores for app + revenue-at-risk (refit scaler on full set)
    feats = build_features(df)
    full_scaler = StandardScaler().fit(feats)
    df_out = df.copy()
    df_out["churn_probability"] = final_model.predict_proba(feats)[:, 1]
    df_out["risk_level"] = df_out["churn_probability"].map(mdl.risk_band)
    df_out.to_csv(out / "churn_predictions_all.csv", index=False)

    explainer = exp.get_explainer(final_model, feats.head(300), final_name)
    global_imp = exp.global_importance(explainer, feats.head(600), top_n=12)
    global_imp.to_csv(out / "shap_global_importance.csv", index=False)

    rav = mdl.revenue_at_risk(df_out)
    (out / "revenue_at_risk.json").write_text(
        json.dumps({k: (v if not isinstance(v, pd.Series)
                        else v.head(5).to_dict()) for k, v in rav.items()},
                   indent=2, default=str))

    for f, obj in [("final_model.pkl", final_model), ("explainer.pkl", explainer),
                   ("scaler_full.pkl", full_scaler)]:
        with open(mdir / f, "wb") as fh:
            pickle.dump(obj, fh)
    (mdir / "meta.json").write_text(json.dumps(
        {"final_model": final_name, "threshold": FINAL_THRESHOLD,
         "high_risk": mdl.HIGH_RISK, "medium_risk": mdl.MEDIUM_RISK}, indent=2))

    return {"out": out, "sp": sp, "df": df, "feats": feats, "df_out": df_out,
            "models": models, "final_model": final_model, "final_name": final_name,
            "explainer": explainer, "scaler": full_scaler, "prob_test": prob_test,
            "thr": thr, "err": err, "rav": rav, "FINAL_THRESHOLD": FINAL_THRESHOLD}

def stage_genai(ctx: dict, live: bool) -> dict:
    """Copilot evaluation: identical cases across all three prompt versions,
    plus negative grounding tests. Works offline via the template fallback."""
    out = ctx["out"]
    cases = ev.build_eval_cases(ctx["sp"], ctx["df"], ctx["prob_test"], n=30)
    provider = LLMProvider() if live else LLMProvider(api_key="")
    results = ev.run_evaluation(cases, ctx["df"], ctx["final_model"],
                                ctx["explainer"], ctx["scaler"], ctx["final_name"], provider)
    results.to_csv(out / "genai_evaluation_results.csv", index=False)
    summary = ev.summarize_evaluation(results)
    summary.to_csv(out / "genai_evaluation_summary.csv", index=False)
    neg = ev.run_negative_tests(provider)
    neg.to_csv(out / "genai_negative_tests.csv", index=False)
    return {"results": results, "summary": summary, "negative": neg, "provider": provider}


def report(ctx: dict, genai: dict) -> None:
    cv = pd.read_csv(ctx["out"] / "churn_cross_validation.csv")
    metrics_df = pd.read_csv(ctx["out"] / "churn_model_metrics.csv")
    gimp = pd.read_csv(ctx["out"] / "shap_global_importance.csv")
    thr, err, rav = ctx["thr"], ctx["err"], ctx["rav"]
    clean = lambda o: json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                  for k, v in o.items()}, indent=2)
    print("\n=== CROSS-VALIDATION (5-fold, train) ===")
    print(cv.to_string(index=False))
    print("\n=== HELD-OUT EVALUATION ===")
    print(metrics_df.to_string(index=False))
    print("\n=== THRESHOLD SEARCH ==="); print(clean(thr))
    print(f"\nFINAL model: {ctx['final_name']} | threshold: {ctx['FINAL_THRESHOLD']:.3f}")
    print("\n=== ERROR ANALYSIS ==="); print(json.dumps(err["counts"]))
    for t in ("FP", "FN"):
        print(f"{t}: {json.dumps(err['profiles'][t])}")
    print("\n=== REVENUE AT RISK ===")
    print(f"  flagged high-risk: {rav['flagged_customers']} | "
          f"expected monthly $ at risk: {rav['expected_monthly_revenue_at_risk']} | "
          f"gross monthly exposure: {rav['gross_monthly_exposure_flagged']}")
    print("\n=== GLOBAL SHAP (top 8) ===")
    print(gimp.head(8).to_string(index=False))
    print("\n=== GENAI EVALUATION SUMMARY ===")
    print(genai["summary"].to_string(index=False))
    print("\n=== NEGATIVE GROUNDING TESTS ===")
    print(genai["negative"].to_string(index=False))
    print("\nAll artifacts written to outputs/ and models/.")


def main(live: bool = False) -> None:
    df = add_tenure_band(load_and_clean())
    ctx = stage_ml(df)
    genai = stage_genai(ctx, live)
    report(ctx, genai)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="Use the live Groq/OpenAI API (needs GROQ_API_KEY).")
    args = ap.parse_args()
    main(live=args.live)