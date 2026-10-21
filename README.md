<div align="center">

# Data Analytics Portfolio
### Turning Raw Data into Business Strategy

[![Tests](https://img.shields.io/badge/Tests-50_Passed-success?style=for-the-badge&logo=pytest&logoColor=white)](#featured-analytical-projects)
[![Records](https://img.shields.io/badge/Records-179K%20verified-00C7B7?style=for-the-badge&logo=database&logoColor=white)](#portfolio-at-a-glance)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Excel](https://img.shields.io/badge/Excel-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white)

</div>

> **Start here → [💰 Weekly Revenue Reconciliation Engine](./weekly-revenue-reconciliation-engine/)** — 128,976 Amazon marketplace transactions reconciled week over week: ₹7.86 cr gross vs ₹1.86 cr actually realized, with ₹82 L+ of cancellation and return leakage isolated and audited. Deterministic engine (no ML), 3-tab Excel + 4-page Streamlit cockpit, **28/28 tests pass**.
>
> **Data-engineering capstone → [🛡️ Pipeline Contract Agent](./pipeline-contract-agent/)** — contract-first guard for the supply-chain log. The contract enforces, the agent investigates, the human approves. Bad batch → quarantine → incident report → `fix.patch` + MR. **22/22 tests pass**, works fully offline.

---

**I answer business questions with data — including the ones where the answer is "don't do it."**

Four end-to-end analytics projects covering **179,010 records**: a supply-chain P&L and
fulfilment audit, a ride-demand and pricing analysis, subscription-retention analytics, and an
Amazon marketplace weekly revenue reconciliation and leakage audit. Every figure below is
reproducible from the committed SQL and Python in this repository.

As a **B.Sc IT graduate** and **Data Analyst**, I specialize in translating complex datasets into clean, reliable, and actionable business insights that drive real decisions.

---

## Portfolio at a Glance

| Project | Scale | Stack | Headline Result |
|---------|-------|-------|-----------------|
| **Supply Chain Performance** | 7,991 orders · 47 SKUs | Python · SQL · Excel | ₹7.30 cr net revenue / ₹2.12 cr profit analysed; late delivery proven systemic, not warehouse-specific |
| **Uber Trip Demand** | 35,000 trips | MySQL · Python · Power BI | 5–7 PM carries 31.2% of demand; airport trips are 39.6% of volume but 54.8% of revenue |
| **Subscription Retention** | 7,043 customers (7,032 analysed after removing 11 blank-`TotalCharges` rows) | Python · SQL · Excel | 26.6% churn; month-to-month + fiber = 72% of revenue at risk |
| **[💰 Weekly Revenue Reconciliation Engine](./weekly-revenue-reconciliation-engine/)** *(finance capstone — start here)* | 128,976 orders · 14 fiscal weeks | Python · Pandas · openpyxl · Streamlit | ₹7.86 cr gross vs ₹1.86 cr net realized (23.7% clearance); ₹82 L+ cancellation/return leakage isolated, Excel + cockpit dashboard, 28/28 tests pass |
| **[🛡️ Pipeline Contract Agent](./pipeline-contract-agent/)** *(data-engineering capstone)* | 7,991 supply-chain orders + drift batches | Contract YAML · Pandas · FastAPI · Streamlit · Groq ReAct | Deterministic gate → quarantine → agent report → `fix.patch` + MR — contract enforces, agent investigates, human approves, 22/22 tests pass |

> **60-second recruiter tour (analyst):** open the [Revenue Engine](./weekly-revenue-reconciliation-engine/) → **Executive Summary** (₹7.86 cr gross → ₹1.86 cr net) → **Weekly Trends** (14 fiscal weeks) → **Leakage Analysis** (₹82 L+ cancellation + return) → **Exception Audit** (every row traceable).
>
> **60-second tour (data engineer):** open the [Contract Agent](./pipeline-contract-agent/) → run `fixtures/bad_money.csv --auto-investigate` → show `validation.json` (`non_numeric_money [high]`) → `incident_report.md` (rule → cause → impact → fix) → `fix.patch` (per-rule guardrail, human approves).

---

## The Real-World Data Analyst Lifecycle: Problem → Methodology → Finding → Decision

In an enterprise setting, analytics projects do not begin with a Jupyter notebook — they begin with an **executive business problem**. Here is how my analytical workflows bridge the gap between raw data, statistical analysis, and boardroom strategy:

| Executive Business Problem | How I Solved It (Methodology & Stack) | Analytical Finding (Data Truth vs. Illusion) | Post-Analysis Decision & Action |
|:--|:--|:--|:--|
| **"Half our orders are late — which warehouse should we overhaul?"** | Ingested 7,991 orders into MySQL; calculated `STDDEV_SAMP()` and decomposed delivery variance using ANOVA principles. | **None — it's systemic.** Only **0.08%** of delivery variance is between warehouses; each facility exhibits an identical 2.82–2.88 day spread. | **Killed the planned per-warehouse capital overhaul.** Diverted engineering focus to upstream supplier scheduling and 3PL carrier dispatch SLAs. |
| **"Isn't warehouse NMK1003 the worst offender in the network?"** | Ran window share queries comparing normalized share of late deliveries against normalized share of total order volume. | **No — pure volume illusion.** NMK1003 accounts for 31.9% of late orders simply because it processes 31.4% of total volume. Its late rate is average. | **Established data governance rules** requiring all operational facility metrics to be volume-normalized before performance reviews. |
| **"Are discounts destroying our margins? Should we cap them?"** | Binned 7,991 transactions into discount tiers (`CASE WHEN`) and analyzed realized profit vs gross revenue in Python & SQL. | **Yes, above 20%.** Orders with $\ge 20\%$ discount yield only **4.64% margin** vs. **31.02%** in the 5–10% band (373 orders were net loss-makers). | **Implemented an executive pricing floor** capping maximum discount allowance at 15% without VP-level authorization. |
| **"When should our ride-hailing app surge-price and incentivize drivers?"** | Processed 35,000 trips in MySQL; used `LAG()` window functions to isolate demand acceleration from raw trip volume. | **5–7 PM carries 31.2% of demand**, but fare revenue *accelerates* at **5 PM (+138%)** on top of +75.5% trip growth, an hour before the 6 PM volume peak. | **Shifted driver surge incentives to 4:30 PM**, mobilizing fleet supply an hour earlier to capture the evening rush before stockouts occur. |
| **"Do higher-rated drivers earn more per trip?"** | Audited ratings across distance bands in Python (`Seaborn` correlation matrix + SQL `CASE WHEN` rating buckets). | **No — confounded metric.** Lower-rated drivers show higher fares only because they drive longer trips (18.9 km vs 16.3 km). Fare/km is flat at ₹22. | **Prevented penalizing drivers on rating alone.** Re-focused customer experience audits on fatigue and ride quality during long journeys. |
| **"Can we cut operational costs by focusing on only our top 2 pickup zones?"** | Built running total Pareto queries (`SUM() OVER`) in MySQL across 5 metropolitan pickup sectors. | **No — 80/20 rule fails here.** It takes **4 of 5 zones** to reach 80% of revenue; only the Airport stands out (27.6% share). | **Maintained city-wide fleet positioning.** Abandoning lower-density zones would have immediately shed 45%+ of gross revenue. |
| **"Sales have been flat for the last six months — what happened, and what do we do?"** | Split half-year windows into volume vs price vs mix (`net_revenue = orders × units × ASP`), then decomposed ASP into gross price and discount factor. Added a discount-band mix counterfactual and a SKU-level price/volume reconciliation. | **Revenue is flat, not down — but profit fell 4.09%.** Net revenue **+0.50%** while profit dropped **₹1.69 lakh** and margin fell **134 bps**. Orders **+4.94%** and units **+4.84%**: demand *grew*. ASP fell **4.14%**, of which **−3.97 pp** is gross price and only **−0.18 pp** is discount. | **Killed the proposed demand-generation campaign** — it treats a symptom that doesn't exist. Redirected the budget to a pricing review of Distributor (−4.17 pp margin) and Online (−1.67 pp), and to discount-approval audits at WARE-PUJ1005. |
| **"Is deep discounting the real cause of the margin drop — and was late delivery to blame?"** | Ran a discount-band mix counterfactual (re-weight 2020H2 band margins by the 2019H2 revenue mix) and tracked the on-time rate across all three half-year windows. | **Discounting is a real but partial cause; delivery is not.** Revenue in the 20%+ band grew **13.03% → 16.79%** of net revenue; reverting the mix would have held margin at **28.62%** instead of 28.10% — the shift alone cost **52 bps ≈ ₹73,617**. On-time delivery went **49.4% → 52.3% → 48.5%** and late-order revenue exposure stayed flat at ~50% in every window. | **Set a product-level profit floor instead of a blanket discount cap** (the 5–10% band realises ~33% margin and is healthy). Kept delivery on a **separate workstream** — it is the largest exposure but did not cause the plateau. |
| **"Are we exposed to losing one big customer? Should we build a key-account programme?"** | Computed revenue concentration by customer and store using the Herfindahl index and effective number of counterparties (`1/HHI`). | **No — there is no key account to protect.** The largest of 50 customers is **2.75%** of net revenue, the top 5 are **12.35%**, HHI is **203** → **49.3 effective customers of 50**. The top store of 367 is **0.6%**. | **Declined to build a key-account programme** and redirected the effort to pricing, where the money actually leaks. Concentration analysis exists to *rule risks out*, not just to find them. |
| **"Which sales team is actually costing us margin — and is it a pricing problem?"** | Aggregated margin by sales team, then tested the mechanism with correlations against each team's average discount versus ASP. | **A 5.03 pp margin spread across 28 teams, driven by discount behaviour.** Best team **31.55%** margin at 11.11% average discount vs worst team **26.52%** at 11.63%. Margin correlates **−0.638** with discount but only **+0.103** with ASP, and order counts are near-equal (1.4×), so it is not a mix effect. | **Gated discount approvals for the bottom-5 teams** (9, 18, 1, 2, 12) instead of running a generic sales incentive. Bringing them to the median margin adds **₹2,45,957 (1.16% of total profit)**. |
| **"Is the evening revenue peak a real surge-pricing effect, or just more trips?"** | Compared fare-per-km by hour, then re-ran the whole analysis with airport trips removed to test the obvious confounder. | **A genuine price premium — and it survives the control.** Peak hours earn **₹26.25/km vs ₹19.39/km** (+6.86). Airport share is near-identical in peak vs quiet hours (**39.96% vs 39.61%**), and on non-airport trips alone the premium is **₹27.23 vs ₹20.02** — **105% of the headline effect survives**. | **Recommended pricing the peak window explicitly** (~35% per km currently captured implicitly), rather than assuming the volume peak is the whole story. |
| **"Is churn a price problem — do customers leave because they pay more?"** | Binned customers into monthly-charges quartiles and compared churn rates. | **No — and the relationship is not even monotonic.** Churn by quartile is **11.32% → 24.59% → 37.55% → 32.88%**. The *most expensive* quartile churns **4.67 pp less** than the third. | **Rejected blanket discounting to retain customers** — it would have added cost without saving revenue. Redirected to contract structure and onboarding. |
| **"Is paperless billing a real churn driver, or just a proxy for contract and payment method?"** | Compared churn with and without paperless billing **within every contract × tenure-band × payment-method cell**, so all three confounders are held constant at once. | **Real — it survives a triple control.** Uncontrolled, paperless churns **33.59% vs 16.38%**, but paperless is also over-represented on month-to-month plans and on electronic-check accounts. Holding contract, *tenure and payment method* constant at once, paperless still churns worse in **31 of 38 cells** (mean lift **+8.30 pp**; month-to-month / 0–12 mo / electronic check: **67.8% vs 50.2%**). The effect holds *within* every single payment method. | **Reframed paperless billing as a product defect to fix** — first-payment failures, card expiry, refund friction — rather than a segment to target. A cheap, high-leverage fix the churn-rate table would have hidden. |

**Notice the pattern:** Several of these analyses concluded with **"don't act" or "stop the planned initiative."** In the real world, knowing what *not* to fund saves more capital than launching unvalidated projects. Every finding here is reproducible from the committed SQL, Python and Excel in this repository.

---

## Core Analytical Skills & Tools

| Category | Technologies & Libraries | Key Methodologies |
| :--- | :--- | :--- |
| **Languages** | Python, SQL (MySQL / PostgreSQL), HTML/CSS | Exploratory Data Analysis (EDA), Statistical Analysis |
| **Data & Stats Libraries** | Pandas, NumPy, SciPy (`stats`), Matplotlib, Seaborn | Hypothesis Testing (Chi-Square, $p$-values, Cramér's V), ANOVA Variance Decomposition, Outlier Auditing |
| **Machine Learning** | Scikit-learn (`RandomForestRegressor`, Classifiers, `train_test_split`) | Predictive Modeling, Feature Engineering, Label Encoding, Metric Evaluation ($R^2$, RMSE) |
| **BI & Visualization** | Power BI, Microsoft Excel, openpyxl, Power Query, Pivots | Interactive Dashboard Design, Executive KPI Reporting, Star Schema Data Modeling |
| **Development Workflow** | Jupyter Notebooks, Git & GitLab, Streamlit, PowerShell / Bash | Automation Scripting, ETL Pipeline Construction, Reproducible Workflows |
| **SQL Techniques** | CTEs, `LAG()`, `RANK()`, `ROW_NUMBER()`, running `SUM() OVER`, `STDDEV_SAMP` | Cohort Banding, Pareto Analysis, Deduplication Pipelines, Trend Detection |
| **AI Engineering** | Streamlit, LangGraph ReAct agents, Groq LLMs, Plotly | Deterministic-first design, glass-box validation, offline fallbacks |

> Skill proof: the [Revenue Engine](./weekly-revenue-reconciliation-engine/) uses all three layers — deterministic pandas for every number (never hallucinated), Plotly for charts, and an optional LLM only for narrative enrichment.

---

## Featured Analytical Projects

> 🖱️ **Don't want to read? [Run the Revenue Engine](./weekly-revenue-reconciliation-engine/)** — the finance capstone below has a 4-page interactive cockpit over 128,976 real orders.

### 1. [Inventory & Logistics Performance Analytics](./supply-chain-performance-analysis/)

![Supply Chain Dashboard](./supply-chain-performance-analysis/image/Supplychain_Dashboard_screenshot.png)

*An end-to-end operational analytics project featuring a Python data cleaning pipeline, custom SQL metrics, and an automated, fully interactive 10-chart Excel dashboard.*
* **Business Challenge:** Half of all orders miss the 5-day delivery target, with ₹3.63 cr of net revenue exposed — and leadership needs to know whether to invest in a specific warehouse or the network.
* **Tech Stack:** Python (Pandas, openpyxl), SQL (MySQL — CTEs, `STDDEV`, `LAG`, window functions), Statistical Variance Decomposition (ANOVA principles), Microsoft Excel (native charts and Pivot Tables).
* **Key Achievements:**
  * **Disproved the obvious answer via statistical hypothesis testing ($H_0$).** Ranking warehouses by late-order count blames the largest site; ANOVA-style variance decomposition shows only **0.08%** of delivery-time variance is between warehouses. Prevented a misdirected improvement programme.
  * Cleaned and processed raw transactional data, generating consistent net revenue, **Delivery Days**, **Order-to-Ship Days**, and **Profit Margins** (₹7.30 cr net revenue / ₹2.12 cr profit across 7,991 orders).
  * Implemented an automated Excel workbook generator (`build_excel_dashboard.py`) using `openpyxl` with dynamic dropdown selectors, date-range inputs, and custom formula-driven pivot tables.
  * Designed an executive **Summary** sheet containing KPI cards, performance grids, and narrative insights on fulfilment performance.
  * Used **ABC Classification** to segment the 47-SKU catalogue by net-revenue contribution (A-items = 80.6% of net revenue) — with an honest read that this catalogue shows only moderate, not textbook 80/20, concentration.
  * **Answered the question every revenue owner asks — "why did sales stall?"** — with a volume/price/mix root-cause decomposition (`src/revenue_root_cause.py`). Revenue is **flat (+0.50%)**, not down, while profit fell **4.09%**: orders grew **4.94%** but ASP fell **4.14%**. SKU-level reconciliation proves **price**, not volume or assortment, drove the plateau.
  * **Ruled out a risk that wasn't there** — revenue concentration analysis (`src/customer_concentration_analysis.py`, Herfindahl **203** → **49.3 effective customers of 50**) proves no key-account programme is needed — and found the **5.03 pp** sales-team margin spread is a **discount-behaviour** gap (margin correlates **−0.638** with discount, only **+0.103** with ASP).
  * Shipped a reproducible Python pipeline (`src/data_cleaning.py`, `src/analytics.py`, `src/revenue_root_cause.py`, `src/customer_concentration_analysis.py`, `src/build_excel_dashboard.py`) so every quoted figure regenerates from the raw data.

### 2. [Ride Demand & Revenue Analytics](./uber-trip-demand-analysis/)

![Uber Power BI Dashboard](./uber-trip-demand-analysis/image/PowerBi_Dashboard.png)

*A comprehensive revenue, behavioral, and predictive analysis of ride-sharing transactions using SQL data warehousing, Python visualization, Scikit-learn modeling, and Power BI dashboarding.*
* **Business Challenge:** Identifying when to surge-price, where to position premium vehicles, and which fleet tier to grow across 35,000 trips.
* **Tech Stack:** MySQL (window functions, CTEs, `LAG`, running totals), Python (Seaborn, Matplotlib), Scikit-learn (`RandomForestRegressor`), Advanced Excel, Power BI.
* **Key Achievements:**
  * Used `LAG()` to separate peak *volume* from peak *growth* — fare revenue accelerates at **5 PM (+138%)** over +75.5% trip growth, an hour before the 6 PM volume peak, moving the incentive trigger an hour earlier.
  * Caught a confounded metric: lower-rated drivers appear to earn more, but the effect vanishes once trip distance is controlled for (**fare-per-km flat at ₹22.06–22.41**).
  * Quantified that **airport trips are 39.6% of volume but 54.8% of revenue** (₹535.77 vs ₹289.40 avg fare).
  * Built a MySQL schema over 35,000 records with `ROW_NUMBER()` deduplication and null validation.
  * Built a **Machine Learning predictive fare model** with Scikit-learn (`RandomForestRegressor`, train-test split, label encoding) evaluated with RMSE and $R^2$ to capture multi-variable fare and duration dynamics.
  * Conducted vehicle-category analysis measuring revenue per ride and revenue-to-distance efficiency (Uber Black ₹40.06/km vs Uber Pool ₹14.08/km).
  * **Proved the evening peak is a real price premium, not a mix artefact** (`src/surge_pricing_analysis.py`). Peak hours earn **₹26.25/km vs ₹19.39/km**; with airport trips removed the premium is *larger* (**₹27.23 vs ₹20.02**) — **105% survives** the control — so ~35% per-km is being captured only implicitly. Ruled out driver concentration as a risk (HHI **100.3** → **99.7 effective drivers**).
  * Reported three **negative findings** (no weekend fare effect, no seasonality, no zone concentration) that removed unjustified recommendations from an earlier draft.

### 3. [Subscription Retention Analytics](./subscription-retention-analytics/)

![Churn Dashboard](./subscription-retention-analytics/image/Churn_Dashboard_screenshot.png)

*End-to-end churn risk and revenue-at-risk analysis on 7,032 customers (7,043 loaded, 11 blank-`TotalCharges` rows removed), delivered through a custom Python pipeline, SQL cohort analysis, and an interactive Excel dashboard.*
* **Business Challenge:** A subscription business is losing ~26% of customers. Which customers leave, when, why, and what revenue is exposed — so retention spend can be prioritised by dollars saved, not by gut feel.
* **Tech Stack:** Python (Pandas, Seaborn, openpyxl), SQL (MySQL — `LAG`, `RANK`, `STDDEV_SAMP`, CTEs), Microsoft Excel (native charts, filterable table), Jupyter.
* **Key Achievements:**
  * Built a 5-KPI, 6-chart executive Excel dashboard with a left-side Filters panel matching the supply-chain reference style — native, filterable, formula-driven from the ChartData sheet.
  * Identified **Month-to-month contracts churn at 42.7%** versus near-zero on two-year plans (chi-square = 1179.5, Cramér's V 0.41) and quantified that **month-to-month + fiber-optic = 72% of revenue at risk**.
  * Caught a confounder: fiber-optic customers churn more, but a large part of the effect is the contract mix, not the service itself — the dashboard splits the two.
  * **Killed a false price story and proved a real billing driver** (`src/churn_driver_analysis.py`). Churn by charge quartile is **non-monotonic** (11.32% → 24.59% → 37.55% → 32.88%) — the most expensive quartile churns *less* — while paperless billing survives a contract × tenure × payment-method triple control (worse in **31 of 38 cells**, mean lift **+8.30 pp**). Priced a 1 pp churn reduction at **$4,557/month**.
  * **Corrected three claims with stronger evidence.** Seniors are *not* immaterial (41.68% vs 23.65%, surviving every control), dependents churn *less* (15.53% vs 31.28%), and the old "negative findings" were under-tested — each is now tested against its confounders.


### 4. [Weekly Revenue Reconciliation Engine](./weekly-revenue-reconciliation-engine/)

*The finance capstone over 128,976 real Amazon marketplace transactions: how much of the
money actually reached us, week over week, and exactly where the rest leaked.*
* **Business Challenge:** "We invoiced ₹7.86 cr last quarter — but cash in the bank says ₹1.86 cr. Where did the other ₹6 cr go?" Most marketplaces cannot answer this weekly, so leakage stays invisible until year-end.
* **Tech Stack:** Python (Pandas, PyArrow), YAML config, openpyxl (3-tab Excel with live formulas), Plotly + Streamlit (4-page cockpit), Docker, GitLab CI + GitHub Actions, Ruff + MyPy + Pytest.
* **Key Achievements:**
  * **Deterministic rules engine, no ML:** 13 order states classified into Net Realized / Cancellation / Return / Loss / In-Transit / Pending across 14 fiscal weeks — every number is auditable `SUM()` math, so a reviewer can trace it back to a row.
  * **Separated true leakage from settlement lag:** ₹82 L+ of genuine cancellation + return leakage (18,334 cancelled orders = ₹69.18 L) is isolated from ₹5.10 Cr that is merely In-Transit — *not* loss. A ₹7.86 cr gross vs ₹1.86 cr net realized split (23.7% clearance) is the headline.
  * **Anomaly detection that fires on business rules:** settled clearance < 70% → CRITICAL, leakage share > 35% → WARNING, week-over-week net drop > 10% → ALERT (12 triggers raised across the period).
  * **Exec-ready deliverables:** a 3-tab Excel workbook (Executive Dashboard, Weekly Trends, Exception Audit) with live formulas and native charts, plus a 4-page Streamlit cockpit — both from one command.
  * **Exception audit trail:** every leakage row is exported to a reviewable `exception_audit.csv` so finance can act on the specific order, not just the aggregate.
  * **28 offline-safe tests** (`pytest`) + clean Ruff and MyPy passes.
* **Try it:** `cd weekly-revenue-reconciliation-engine; python run_pipeline.py` → Excel workbook + exception audit; `streamlit run streamlit_app/Dashboard.py` → the cockpit.


### 5. [Pipeline Contract Agent](./pipeline-contract-agent/)

*The data-engineering layer that keeps the analytics trustworthy: a contract-first
pipeline guard for the supply-chain order log. **The contract enforces, the agent
investigates, the human approves.***
* **Business Challenge:** When a source quietly changes format (ISO dates instead of DD/MM/YY slashes, text in money fields, null customer IDs), cleaned tables still load — but every downstream KPI is silently wrong. Catch it before load, and turn every failure into an investigated, fixable incident.
* **Tech Stack:** Python (Pandas), YAML data contract (sha-pinned, versioned), FastAPI, Streamlit, LangGraph ReAct agent + Groq (optional live investigation), Docker, GitHub Actions (tests on push + scheduled daily batch), GitLab CI.
* **Key Achievements:**
  * **Deterministic validation, zero AI in the gate:** 8 rule families (nullability, date-format allowlist, money parsing, warehouse/channel allowlists, uniqueness, R01 date chronology) — identical input always yields identical verdict.
  * **Fail-safe routing:** PASS → SQLite warehouse with load metadata; FAIL → batch quarantined untouched with `validation.json` + manifest (audit trail), never deleted.
  * **AI agent as response layer:** on breach, an investigator maps each broken rule to root cause → pipeline location → downstream impact → fix; Groq upgrades the narrative only. Emits `incident_report.md` + `fix.patch` + MR body (dry-run default; human applies).
  * **Deploy-shaped:** FastAPI `POST /ingest` (200 pass / 422 quarantined + report), operations console, `docker compose up`, CI runs the suite and a daily drift-injected batch.
  * **22 offline-safe tests** — every rule has a pass and a fail case; no API key needed.
* **Try it:** `cd pipeline-contract-agent; pytest -q; python -W ignore pipeline/ingest.py --batch fixtures/bad_money.csv --auto-investigate`

---

## 🤝 AI-Assisted Workflow & Validation Gates

AI accelerates every stage of my pipeline — it does not decide what ships. Each AI-assisted step passes a human validation gate before its output is trusted:

| Stage | AI Assists With | My Validation Gate |
| :--- | :--- | :--- |
| **Data cleaning** | Drafting dedup / null-handling logic | Row-count reconciliation against source; spot-checks on edge cases |
| **SQL analytics** | Query scaffolding & window-function drafts | Every query executed and its output reconciled with Python cross-checks |
| **EDA & visuals** | Chart selection, formatting, narrative drafts | Distribution and correlation checks that confirm or *challenge* the AI's framing |
| **Dashboards** | Layout scaffolding, DAX snippets | KPI figures traced back to committed SQL — no number ships unverified |
| **Documentation** | README structure & prose polish | Technical walkthroughs reviewed line-by-line against actual code behavior |

The principle: **AI is a co-pilot, not an oracle.** It drafts, I verify — because a hallucinated SQL window function that *looks* right is more dangerous than one that obviously fails. My headline findings (0.08% between-warehouse variance, flat ₹22/km fare-per-km) all survived validation that would have caught AI shortcuts.

---

## Repository Architecture

Each directory is fully self-contained, including its own documentation, SQL scripts, raw/cleaned datasets, and Jupyter analysis files:

```bash
data-analytics/
│
├── pipeline-contract-agent/ # 🛡️ DATA-ENGINEERING CAPSTONE — contract-first guard
│ ├── contract/ # supply_orders.contract.yaml (v1.0.0, sha-pinned law)
│ ├── src/ # validate (deterministic, NO AI) / trigger / investigate / report / mr
│ ├── pipeline/ingest.py # CLI: validate -> quarantine/pass -> investigate
│ ├── api/main.py # FastAPI: POST /ingest (200 pass / 422 quarantine)
│ ├── app.py # Streamlit operations console
│ ├── fixtures/ # good + 4 bad batches
│ ├── tests/ # 22 green (validator + pipeline + agent offline)
│ ├── incidents/ # quarantine audit trail (batch + validation + report + patch)
│ └── README.md # 60-second demo + design decisions
│
├── weekly-revenue-reconciliation-engine/ # 💰 finance capstone — weekly reconciliation + leakage audit
│   ├── src/ # reconciliation engine (classifier, metrics, variance, anomalies)
│   ├── streamlit_app/ # 4-page cockpit (exec summary, trends, leakage, exceptions)
│   ├── config/ # settings.yaml (thresholds + bucket map) + logging.yaml
│   ├── data/ # raw + processed datasets (git-tracked)
│   ├── docs/ # architecture, data dictionary, deployment guide, screenshots
│   ├── tests/ # 28 green (loader, engine, metrics, classifier, Excel)
│   ├── scripts/ # Excel capture + waterfall + cockpit renderers
│   └── README.md # findings, known gaps, how to run
│   
│
├── supply-chain-performance-analysis/ # Operational efficiency & inventory dashboards
│ ├── src/ # Reproducible Python pipeline (clean, analytics, excel)
│ ├── data/ # Raw & processed CSV datasets (git-tracked)
│ ├── outputs/ # Generated KPI summary & analysis tables
│ ├── excel_analysis/ # Generated + interactive Excel dashboards
│ ├── powerbi/ # Power BI model guide (DAX measures, layout)
│ ├── sql_queries/ # Database schemas & analytical queries (.sql)
│ ├── image/ # Dashboard screenshots & visual highlights
│ ├── requirements.txt # Python dependencies
│ ├── Supplychain.ipynb # Python EDA & feature engineering notebook
│ └── README.md # Detailed project report and insights
│
├── uber-trip-demand-analysis/ # Ride-sharing demand & fare analytics
│ ├── data/ # Datasets & source structures
│ ├── excel_analysis/ # Excel pivot table summaries
│ ├── sql_queries/ # MySQL data-cleaning and analytics scripts (.sql)
│ ├── powerbi/ # Power BI report (.pbix)
│ ├── image/ # Visual analysis plots & demand curves
│ ├── UberTripAnalysis.ipynb # Interactive Python behavioral analytics
│ └── README.md # Complete project brief and recommendations
│
├── subscription-retention-analytics/ # Customer churn risk and retention analysis
│ ├── src/ # Excel dashboard + screenshot generators
│ ├── data/ # IBM Telco churn dataset
│ ├── outputs/ # Segment analysis tables
│ ├── excel_analysis/ # Native Excel dashboard
│ ├── sql_queries/ # MySQL cleaning and churn analysis
│ ├── image/ # EDA and dashboard visuals
│ ├── requirements.txt # Python dependencies
│ └── README.md # Detailed retention analysis
│
└── README.md # Main portfolio lander (this file)
```

---

## Contact & Collaboration

I am actively seeking entry-level **Data Analyst**, **Business Intelligence Analyst**, or **Data Engineer** roles where I can help teams turn complex data into clean, business-boosting decisions.

<div align="center">

[![Portfolio](https://img.shields.io/badge/Portfolio-Live_Site-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://ansh-thakur-netlify.netlify.app/)
[![Profile](https://img.shields.io/badge/GitLab-Profile-FC6D26?style=for-the-badge&logo=gitlab&logoColor=white)](https://gitlab.com/ansht_121)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ansh-thakur-5407192b4/)
[![Email](https://img.shields.io/badge/Email-ansht1194@gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:ansht1194@gmail.com)

</div>

Feel free to browse my code, download the interactive Excel dashboards to explore their dynamic filters, or connect with me on LinkedIn!
