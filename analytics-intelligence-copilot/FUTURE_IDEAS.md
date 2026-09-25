# 🔒 FUTURE IDEAS — Saved Blueprint (Build AFTER the core agent is validated)

> Status: **SAVED / LOCKED**. These features are deliberately NOT built yet.
> Rule: the core agent (dataset switcher + quick-insight chips + chat Q&A +
> executive brief) must run end-to-end first. Only then unlock these one by one.

## 1. 🎛️ Interactive "What-If" Scenario Simulator (Prescriptive Analytics)
- Sliders / questions like *"Cap max discounts at 15% — how much margin is recovered?"*
- *"Convert 20% of month-to-month fiber customers to 1-year contracts — annual revenue protected?"*
- Proves ROI thinking and financial modelling, not just backward-looking queries.

## 2. 🎭 Executive Persona Switcher (CFO vs COO vs CMO)
- **CFO mode:** margins, discount leakage, revenue at risk, cash flow.
- **COO mode:** warehouse bottlenecks, delivery variance, lead times, SLA breaches.
- **CMO mode:** churn cohorts, retention, LTV, pricing tiers.
- Shows you can communicate with different business leaders.

## 3. 🧠 Automated 5-Whys Root-Cause Engine
- One click: *"Why is our delivery SLA failing?"* → agent tests hypotheses in data
  (warehouses? shipping lag? procure-to-order on specific SKUs?) and outputs a root-cause tree.

## 4. 📊 Autonomous Chart-from-Chat
- Free-form question → agent decides the right Plotly chart and renders it inline
  (currently charts come from deterministic quick-insight chips only).

## 5. 📄 PDF Executive Brief Export
- One-click brief currently downloads as Markdown; add styled PDF export for stakeholders.

## 6. 🧬 Semantic / Vector Retrieval Layer
- Swap/augment TF-IDF-style keyword matching with embeddings + FAISS for
  cross-dataset semantic search ("show me every margin problem across all domains").

## Unlock checklist (per idea)
1. Small prototype on ONE dataset.
2. Validate every number against the committed SQL/Python in this repo.
3. Add the UI control + docs + interview talking point.
4. Commit separately — one idea per commit.
