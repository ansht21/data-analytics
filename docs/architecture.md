# Architecture — Weekly Revenue Reconciliation Engine

## Data Flow

```
data/raw/Amazon_Sale_Report.csv (128,976 rows)
        │
        ▼
src/data_loader.py  ── 11-step cleaning pipeline
        │              (drop dead cols → mixed dates → null Amounts →
        │               currency/state/postal cleanup → FBA impute →
        │               fiscal tagging W13–W26 → bucket mapping →
        │               schema validation → parquet export)
        ▼
data/processed/cleaned_transactions.parquet
        │
        ├──────────────────────────────┐
        ▼                              ▼
src/reconciliation/              src/reconciliation/
  engine.py                       variance_analyzer.py
  (weekly Gross/Net/KPIs)        (WoW growth + anomaly rules)
        │                              │
        ▼                              ▼
src/reporting/  ── openpyxl 3-tab workbook → reports/*.xlsx
streamlit_app/  ── 4-page Plotly dashboard → :8501
```

## Layers

| Layer | Modules | Responsibility |
|:---|:---|:---|
| Config | `src/config.py`, `config/settings.yaml` | Typed dataclass settings; no hardcoded paths/thresholds |
| Logging | `src/logger.py`, `config/logging.yaml` | Rotating file + console, single factory |
| Ingestion | `src/data_loader.py` | 11-step cleaning, schema validation, parquet |
| Domain | `reconciliation/*` | Fiscal calendar, bucket classification, KPI math, anomalies |
| Reporting | `reporting/*` | Excel workbook (KPI cards, formulas, charts, conditional formats) |
| Dashboard | `streamlit_app/*` | Interactive Streamlit + Plotly drill-down + CSV export |
| CLI | `run_pipeline.py` | `--week`, `--output-dir`, `--no-excel` |
| Quality | `tests/*`, `.gitlab-ci.yml` | pytest + coverage ≥ 80%, Ruff, MyPy, Docker build |

## Anomaly Rules (config-driven)

Rules apply to the **settled base** (Net Realized + true leakage), not to
gross invoiced — gross-based coverage is dominated by In-Transit settlement
lag and would flag every single week.

- **CRITICAL** — weekly Settled Clearance % < 70
- **WARNING** — leakage share of the settled base > 35 %
- **WARNING** — weekly Cancellation % > 15
- **ALERT** — WoW Net Revenue growth < −10 %

Partial weeks (fewer than `min_days_for_full_week` observed days) are
excluded from anomaly detection, so truncated window edges cannot raise
false alarms.

## Two Coverage Metrics (do not conflate)

| Metric | Formula | What it answers |
|:---|:---|:---|
| `settled_clearance_rate` | Net Realized / (Net Realized + leakage) | Of the money that reached a final state, how much did we keep? |
| `clearance_rate` (gross coverage) | Net Realized / Gross Invoiced | How much of the invoiced GMV has converted to cash so far? |

In this export ~66 % of GMV is still In-Transit, so gross coverage sits near
24 % while settled clearance is ~69 %. The first is settlement lag, the
second is leakage.

## Single Source of Truth

`src/reconciliation/metrics.py` computes every headline number. The
Streamlit dashboard, the Excel workbook and the PNG renderer all import it,
so a figure can never disagree between surfaces.
