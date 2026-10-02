# 🤖 Analytics Intelligence Copilot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-ReAct_Agent-green)
![Groq](https://img.shields.io/badge/Groq-LLM-orange)
![pandas](https://img.shields.io/badge/pandas-Deterministic_Analytics-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?logo=plotly&logoColor=white)

> **Ask business questions in plain English. Get board-ready answers — with the math to prove them.**

</div>

An **agentic BI assistant** over the three committed datasets in this portfolio
(**50,034 records**): supply-chain orders, Uber trips, telecom churn. Pick a dataset,
tap a one-click insight chip, or ask anything in chat — every answer follows
**Finding → Business explanation → Suggested decision**, with a Plotly chart and an
expandable **"🔍 Inspect logic & query"** panel showing the exact pandas code + runtime.

**Two honest modes** (sidebar banner always says which is active):
- 🟡 **Offline insight mode** (default, zero API key): chips, KPIs, charts, executive brief.
- 🟢 **Live AI chat**: add `GROQ_API_KEY` to `.env` for the LangGraph ReAct agent.

---

## ✨ Features

| Feature | What it does |
|---------|--------------|
| 📂 **Dataset switcher** | Supply Chain (7,991) · Uber (35,000) · Churn (7,043) · or upload CSV/Excel |
| ⚡ **9 quick-insight chips** | One click, zero typing — computed **live in pandas** |
| 📊 **Interactive Plotly charts** | Every insight renders a chart inline |
| 🛡️ **Analytical-trap guardrail** | Warehouse Trap chip catches the volume illusion (31.9% of late orders, 0.08% variance) |
| 🔍 **Glass-box transparency** | Every card shows its pandas snippet + runtime in ms |
| 📄 **Executive brief** | One button → KPIs, findings, risks, decisions + Markdown download |
| 💬 **Live AI chat (optional)** | LangGraph ReAct agent; degrades gracefully offline |
| 🧪 **18 regression tests** | Every chip figure asserted vs committed SQL/outputs (`pytest tests/test_analytics.py -q`) |
| 🟡 **Offline-first** | No API key needed; sidebar banner always shows the active mode |

---

## ✅ Tested 2026-09-26 (what was verified)

| Check | Result |
|-------|--------|
| Fresh `.venv` on **Python 3.11.15** + `pip install pandas==2.2.3 python-dotenv pytest streamlit plotly openpyxl` | Clean install, no errors |
| `pytest tests/test_analytics.py -q` | **18 passed in ~4s** |
| `streamlit run app.py --server.port 8501` (headless) | Server up, no `Error/Traceback/ModuleNotFound` in logs |
| `GET http://localhost:8501` | **HTTP 200** |
| Dataset loads | supply **7,991** · uber **35,000** · churn **7,043** |

> If `streamlit run app.py` fails with `ModuleNotFoundError: No module named
> 'plotly'` (or `pandas`), your `.venv` is empty or on the wrong Python —
> recreate it with Python 3.11 and reinstall `requirements.txt`.
> The empty-`.venv` case is what broke the run on 2026-09-26.

---

---

## 📸 Recruiter walkthrough (60 seconds)

1. Pick **📦 Supply Chain Orders** → KPI cards ($73.0M revenue, 49.5% late).
2. Click **▶ Warehouse Trap Check** → finding + chart + *"don't fund a per-site fix"*.
3. Click **📄 Generate Executive Brief** → full brief + download.
4. Switch to **🚗 Uber** → **▶ Peak Surge Detection** → 5 PM acceleration chart.

---

## 🚀 Getting Started

```bash
cd data-analytics/analytics-intelligence-copilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
copy .env.example .env              # optional — only for live AI chat
streamlit run app.py                # opens http://localhost:8501
```

> **Verified 2026-09-26 on Python 3.11.15** — use Python 3.11 (`requirements.txt`
> pins `pandas<2.3`; pandas 3.x is not supported). After install:
> `pytest tests/test_analytics.py -q` → **18 passed**, `streamlit run app.py` →
> **HTTP 200 on http://localhost:8501**, all 3 datasets load
> (supply 7,991 · uber 35,000 · churn 7,043).
>
> **Offline first:** without `GROQ_API_KEY` the app runs fully offline
> (chips + KPIs + charts + executive brief). The sidebar banner shows
> 🟡 *Offline insight mode*. No `langchain`/`langgraph` install needed for that.
> Add the key to `.env` to unlock 🟢 live AI chat (requires the agent libs).


## 🏗️ Architecture

```
analytics-intelligence-copilot/
├── app.py               # Streamlit UI: switcher, chips, brief, chat
├── src/
│   ├── datasets.py      # registry + loaders reading ../<project>/data/*.csv (no data copied)
│   ├── analytics.py     # 9 deterministic pandas insights (finding/explanation/suggestion/chart/snippet)
│   ├── brief.py         # executive-brief assembler + Markdown renderer
│   └── agent.py         # LangGraph ReAct agent (lazy import) + offline fallback
├── tests/test_analytics.py  # 17 tests: figures asserted vs committed SQL/outputs
├── requirements.txt / .env.example
├── FUTURE_IDEAS.md      # 🔒 saved post-validation roadmap (what-if, personas, 5-whys…)
└── README.md
```

## ✅ Validation (why the numbers are trustworthy)

| Chip claim | Committed source it matches |
|---|---|
| 20%+ discounts → **4.64%** realised margin vs **31.02%** (5–10%) | `supply-chain…/sql_queries/02_sales_analysis.sql` Q8 |
| WARE-NMK1003 = **31.9%** of late orders; **0.08%** between-warehouse variance | `outputs/warehouse_performance.csv` + README |
| **36** A SKUs ≈ 80% of revenue | `outputs/abc_classification.csv` |
| 5 PM **+138% fare-revenue** acceleration (+75.5% trip growth); 6 PM peak; **31.2%** in 5–7 PM | Uber README / revenue SQL |
| Airport **39.6%** volume / **54.8%** revenue | Uber README |
| Churn cohort **2,128 / 54.6%** | `subscription-retention…/outputs/churn_segment_revenue.csv` |
| Electronic check **45.3%** | `subscription-retention…/sql_queries/02_churn_analysis.sql` |
| Churn CSV **7,043 rows** (7,032 after cleaning) | `subscription-retention…/sql_queries/01_data_cleaning.sql` |

Run `PYTHONPATH=. pytest tests/ -q` → **18 passed**.

## ⚠️ Limitations (honest)

- Live chat needs a Groq key + internet; everything else is offline.
- `analyze_data` uses `eval()` on LLM-generated pandas — fine locally, sandbox before sharing.
- Custom uploads get generic KPIs + live chat only (no prebuilt chips for unknown schemas).

## 🔒 What's next (saved, not built)

See **[FUTURE_IDEAS.md](./FUTURE_IDEAS.md)** — what-if simulator, CFO/COO/CMO personas,
5-whys root-cause engine. Locked until the core above is validated end-to-end.

---

*Built by **Ansh Thakur** — every figure traceable to the committed SQL/Python in this repo.*
