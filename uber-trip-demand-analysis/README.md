# 🚖 Ride Demand Forecasting & Revenue Analytics

## 📖 Project Overview
This project performs a comprehensive behavioral and financial analysis of a **synthetic ride-sharing transaction dataset** (35,000 trips, generated for portfolio demonstration). Using a two-stage SQL data cleaning pipeline, multi-dimensional MySQL reporting queries, and Excel pivot dashboards, the project uncovers peak demand windows, identifies high-revenue vehicle categories, and produces actionable pricing and allocation recommendations.

> ℹ️ *Data note: this is a simulated dataset (uniform monthly volume, 5 pickup zones). The workflow and analytical techniques are the deliverable, not real Uber metrics.*

### 🌟 Business Impact Highlights
* **Full Pipeline Coverage:** Built a `ROW_NUMBER()` + `DISTINCT` deduplication safeguard (the source data was already clean, so it removed 0 rows — the value is a reusable, production-style integrity step).
* **Revenue Deep-Dive:** Analyzed fare amounts, distances, and durations across **vehicle types, pickup zones, time periods, and weekend/weekday segments**.
* **Airport Insights:** Quantified airport trip share and its premium fare contribution relative to standard bookings.
* **Operational Recommendations:** Demand heatmap (hourly) used to define surge pricing windows and driver dispatch schedules.

---

## 🛠️ Tech Stack & Technical Architecture
* **MySQL (Window Functions, CTEs, Aggregations):** Two-script SQL pipeline — a dedicated cleaning script followed by a layered business intelligence script covering 8 analytical dimensions.
* **Python (Pandas, Matplotlib, Seaborn):** EDA and visual storytelling in `UberTripAnalysis.ipynb`, including heatmaps, bar charts, and distribution plots.
* **Microsoft Excel (Pivot Tables, Charts):** Summary dashboard for stakeholder-ready reporting covering peak hours, vehicle revenue, and location performance.
* **Power BI:** Interactive `.pbix` dashboard for executive-level KPI monitoring.

---

## 🔄 End-to-End Pipeline Architecture

### 1. Data Cleaning & Deduplication (`sql_queries/01_data_cleaning.sql`)
The raw CSV is loaded into a MySQL staging table and processed through a **two-stage deduplication pipeline**:

* **Stage 1 — Exact Row Deduplication:** `CREATE TABLE ... AS SELECT DISTINCT *` eliminates fully identical records.
* **Stage 2 — Trip-ID Deduplication:** `ROW_NUMBER() OVER (PARTITION BY Trip_ID ORDER BY Date DESC)` retains only the most recent record per trip, handling cases where a booking was re-submitted or updated.
* **Validation Checks:** Post-cleaning queries audit for null `Trip_ID`, `Fare_Amount`, and `Trip_Distance_km` fields to confirm pipeline integrity.

### 2. Business Intelligence Reporting (`sql_queries/02_revenue_analysis.sql`)
Eight layered analytical queries that build from portfolio-level KPIs down to granular segment comparisons:

| Query | Business Question Answered |
| :--- | :--- |
| **Portfolio KPI Summary** | Total trips, revenue, avg fare, avg distance, avg rating |
| **Hourly Demand Heatmap** | Which hours generate the most trips and highest revenue? |
| **Vehicle Performance** | Which vehicle type earns the most per km driven? |
| **Airport Trip Analysis** | What % of trips are airport-bound and at what fare premium? |
| **Pickup Location Comparison** | Revenue across the 5 pickup zones (near-uniform in this dataset) |
| **Weekend vs. Weekday** | Do weekends produce higher average fares? |
| **Time-of-Day Periods** | Morning / Afternoon / Evening / Night demand breakdown |
| **Monthly Revenue Trend** | Seasonal demand cycles and month-over-month growth |

### 3. Visual EDA (`UberTripAnalysis.ipynb`)
Python-driven exploration of cleaned trip data including:
* **Heatmaps:** Hour × Day-of-Week demand matrix to visualize peak traffic windows.
* **Vehicle Revenue Charts:** Side-by-side comparison of total and per-km revenue.
* **Distribution Plots:** Fare and distance histograms to detect outliers and skew.
* **Pickup Location Bar Charts:** Top revenue zones ranked horizontally.

---

## 📊 Core Analytical Insights

### 1. Peak Demand Windows
The hourly demand heatmap shows a clear **evening peak**: the busiest hours are **6 PM (4,053 trips), 5 PM (3,467), and 7 PM (3,411)** — a textbook after-work commute surge. Late-night fares are *not* meaningfully elevated in this data (≈2% above average), so the genuine operational signal is the evening volume spike, not a late-night premium.

### 2. Vehicle Category Revenue Efficiency
* **Revenue-per-km by tier:** Uber Black **₹40.68**, UberXL ₹27.19, Comfort ₹25.89, UberX ₹20.81, Uber Pool ₹14.57. Premium (Black) earns ≈ **1.96× UberX** and **2.79× Uber Pool**.
* **But total revenue tells a different story:** UberX leads total revenue (**₹4.9M**) on sheer volume, while Black is high-margin-per-km but lower volume — a classic premium-vs-volume trade-off.

### 3. Airport Trip Premium
* Airport trips are **39.6%** of bookings (high, reflecting the synthetic data) and carry a real fare premium: **₹535.77 vs ₹289.40** for city trips (≈ **1.85×**) — supporting a dedicated airport dispatch strategy.

### 4. Weekend Fare Behavior
* Weekend vs weekday average fare is **₹389.34 vs ₹386.05** — a **<1% difference**. Honest read: there is *no* material weekend fare effect in this dataset, so a weekend-specific pricing rule isn't justified by the data.

---

## 💡 Business Recommendations

1. **Demand-Based Surge Pricing:** Focus fare multipliers on the **5–7 PM evening peak**, where trip volume is genuinely highest — this is the strongest, data-backed lever.
2. **Airport Fleet Allocation:** With airport trips earning ~1.85× the average fare, pre-position premium/SUV drivers for airport demand to maximise revenue per dispatch.
3. **Premium-vs-Volume Mix:** Keep UberX as the volume/revenue backbone while protecting Uber Black's high per-km margin — don't over-discount the premium tier.
4. **Driver Rating Baseline:** Use the average driver rating (4.32) as a service-quality benchmark; flag drivers consistently below threshold for retraining.

> *Note: an earlier draft recommended a weekend surcharge and late-night surge — the data shows neither effect is real here, so those were removed. Knowing which recommendations the data does **not** support is part of the analysis.*
