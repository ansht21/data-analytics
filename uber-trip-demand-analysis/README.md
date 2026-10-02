# Ride Demand & Revenue Analytics

**Business problem:** A ride-hailing operator needs to know *when* to surge-price, *where*
to position premium vehicles, and *which* fleet tier to grow — using 35,000 trip records.

![Uber Trip Analysis Dashboard](image/PowerBi_Dashboard.png)
*Demand is not spread evenly across the day — a single evening spike drives the business. The hourly bars show ~350 trips at 3 AM against 4,053 at 6 PM.*

> ℹ *Data note: this is a simulated dataset (uniform monthly volume, 5 pickup zones).
> The workflow and analytical techniques are the deliverable, not real Uber metrics.
> Fares are in ₹ (INR) — the dataset uses Indian payment methods including UPI.*

---

## System Design Decisions

| Decision | Rationale |
| :--- | :--- |
| **MySQL warehouse over flat-file analysis** | 35,000 trips × multi-dimension queries (zone × hour × vehicle) need indexed, typed storage with window functions |
| **`ROW_NUMBER()` dedup guard in staging** | Idempotent reloads — rerunning the pipeline can never duplicate trips |
| **`LAG()` for growth vs totals for volume** | Peak-*growth* hour and peak-*volume* hour are different questions; the wrong window function picks the wrong surge window |
| **Power BI delivery layer** | The hour × zone demand matrix stays filterable for the operations team, not just a static image |

## The Story in 3 Charts

1. **The assumption** — `image/uber_zone_pareto.png`: concentrate on the top revenue zones — 80/20 says yes.
2. **The evidence** — `image/uber_hourly_demand.png`: one evening spike carries the day, and growth starts at 5 PM — an hour before the 6 PM volume peak. It takes 4 of 5 zones to reach 80% of revenue, so coverage stays city-wide.
3. **The decision** — `image/uber_vehicle_revenue.png`: Uber Black earns ₹40.06/km versus Pool's ₹14.08 — grow the premium tier on the routes where distance pays.

---

## ▶ How to Run
```bash
pip install pandas numpy matplotlib seaborn jupyter
# 1. Run the SQL queries in order: 01_data_cleaning.sql → 02_revenue_analysis.sql
# 2. Generate visuals: jupyter notebook UberTripAnalysis.ipynb
```
All charts are saved to `image/` by the notebook itself. Power BI report: [`powerbi/UberTrip_Dashboard.pbix`](powerbi/UberTrip_Dashboard.pbix). Excel dashboard: [`excel_analysis/uber_trips_data.xlsx`](excel_analysis/uber_trips_data.xlsx).

---

## Business Questions Answered

Every figure below is reproducible from the committed SQL. Click a query link to verify.

| # | Business Question | Metric Used | Finding | Recommended Action | Query |
|:--|:--|:--|:--|:--|:--|
| **Q1** | When should we surge-price and add drivers? | Trips & revenue by hour | **5–7 PM carries 31.2% of all demand** (10,931 of 35,000 trips) in 3 of 24 hours. Peak hour is 6 PM (4,053 trips). | Concentrate incentives on the 5–7 PM window | [§2](sql_queries/02_revenue_analysis.sql) |
| **Q2** | How dependent are we on airport trips? | Revenue split by airport flag | Airport is **39.6% of trips but 54.8% of revenue** (₹74.3L). Avg fare ₹535.77 vs ₹289.40 — **1.85×**. | Protect airport supply; it is the highest-value corridor | [§4](sql_queries/02_revenue_analysis.sql) |
| **Q3** | Which fleet tier earns most per km? | Revenue ÷ distance by vehicle | Uber Black **₹40.06/km vs Uber Pool ₹14.08/km — 2.8×**. But UberX leads total revenue (₹49.1L) on volume. | Grow Black in premium zones; keep UberX as the backbone | [§3](sql_queries/02_revenue_analysis.sql) |
| **Q4** | Do higher-rated drivers earn more? | Avg fare by rating band | **No — and the obvious read is wrong.** Lowest-rated (<4.0) show the *highest* avg fare (₹419 vs ₹364). Cause is trip length (18.9 km vs 16.3 km), not driver quality: fare-per-km is flat at ₹22.06–22.41 across all bands. | Investigate rider experience on long trips — don't penalise drivers | [§11](sql_queries/02_revenue_analysis.sql) |
| **Q5** | Can we focus on just our top zones? | Cumulative revenue share | **No.** It takes **4 of 5 zones to reach 80%** of revenue. Only Airport stands out (27.6%); the rest sit at 17–19% each. | Keep coverage city-wide; a "top zones" strategy fails here | [§10](sql_queries/02_revenue_analysis.sql) |
| **Q6** | Should weekend pricing differ? | Avg fare by weekend flag | **No.** ₹389.34 vs ₹386.05 — a **0.9%** gap, with near-identical trip distance. | Do not build a weekend pricing tier | [§6](sql_queries/02_revenue_analysis.sql) |
| **Q7** | When does the evening rush actually *start*? | Hour-over-hour trip-volume change (`LAG`) | The query measures trip-volume acceleration separately from revenue, so incentive timing is based on demand rather than fare mix. | Use the highest positive trip-volume jump to schedule incentives; validate operationally | [§9](sql_queries/02_revenue_analysis.sql) |
| **Q8** | Is there visible within-year variation? | Trips and revenue by month | Monthly results describe one simulated year only; they do not establish recurring annual seasonality. | Use time-of-day for current operations; validate seasonality with multi-year production data | [§8](sql_queries/02_revenue_analysis.sql) |

**Three of these eight are negative findings.** Q5, Q6 and Q8 tell the business *not* to
act — which prevents wasted spend. Reporting them is part of the job.

---

## Project Overview
This project performs a comprehensive behavioral and financial analysis of a **synthetic ride-sharing transaction dataset** (35,000 trips, generated for portfolio demonstration). Using a two-stage SQL data cleaning pipeline, multi-dimensional MySQL reporting queries, and Excel pivot dashboards, the project uncovers peak demand windows, identifies high-revenue vehicle categories, and produces actionable pricing and allocation recommendations.

### Business Impact Highlights
* **Full Pipeline Coverage:** Built a `ROW_NUMBER()` + `DISTINCT` deduplication safeguard (the source data was already clean, so it removed 0 rows — the value is a reusable, production-style integrity step).
* **Revenue Deep-Dive:** Analyzed fare amounts, distances, and durations across **vehicle types, pickup zones, time periods, and weekend/weekday segments**.
* **Airport Insights:** Quantified airport trip share and its premium fare contribution relative to standard bookings.
* **Operational Recommendations:** Demand heatmap (hourly) used to define surge pricing windows and driver dispatch schedules.

---

## Tech Stack & Technical Architecture
* **MySQL (Window Functions, CTEs, Aggregations):** Two-script SQL pipeline — a dedicated cleaning script followed by a layered business intelligence script covering 11 analytical dimensions, including `LAG()` trend detection and running-total Pareto analysis.
* **Python (Pandas, Matplotlib, Seaborn, Scikit-learn):** EDA, visual storytelling, and predictive modeling in `UberTripAnalysis.ipynb`, including heatmaps, distribution plots, and fare regression.
* **Machine Learning (Scikit-learn):** Predictive modeling using `RandomForestRegressor` evaluated via RMSE and $R^2$ score to model fare dynamics across trip features.
* **Microsoft Excel (Pivot Tables, Charts):** Summary dashboard for stakeholder-ready reporting covering peak hours, vehicle revenue, and location performance.
* **Power BI:** Interactive `.pbix` dashboard for executive-level KPI monitoring.

---

## End-to-End Pipeline Architecture

### 1. Data Cleaning & Deduplication (`sql_queries/01_data_cleaning.sql`)
The raw CSV is loaded into a MySQL staging table and processed through a **two-stage deduplication pipeline**:

* **Stage 1 — Exact Row Deduplication:** `CREATE TABLE ... AS SELECT DISTINCT *` eliminates fully identical records.
* **Stage 2 — Trip-ID Deduplication:** `ROW_NUMBER()` partitions by `Trip_ID` and uses deterministic date, time, fare, distance, and driver tie-breakers to retain one record per trip. The source does not contain an update timestamp, so the pipeline does not claim to identify the most recently updated record.
* **Validation Checks:** Post-cleaning queries audit for null `Trip_ID`, `Fare_Amount`, and `Trip_Distance_km` fields to confirm pipeline integrity.

### 2. Business Intelligence Reporting (`sql_queries/02_revenue_analysis.sql`)
Eleven layered analytical queries that build from portfolio-level KPIs down to granular segment comparisons. Sections 9–11 use CTEs and window functions to answer questions a plain `GROUP BY` cannot:

| Query | Business Question Answered | Technique |
| :--- | :--- | :--- |
| **1. Portfolio KPI Summary** | What is the overall health of the business? | Aggregation |
| **2. Hourly Demand Heatmap** | Which hours should we surge-price? | `RANK()` |
| **3. Vehicle Performance** | Which vehicle type earns the most per km driven? | Ratio aggregation |
| **4. Airport Trip Analysis** | How much revenue depends on airport trips? | Window share |
| **5. Pickup Location Comparison** | Which zones generate the most revenue? | Aggregation |
| **6. Weekend vs. Weekday** | Should weekend pricing differ? | Aggregation |
| **7. Time-of-Day Periods** | Which part of day contributes most revenue? | Aggregation |
| **8. Monthly Revenue Trend** | Is there a seasonal cycle? | Aggregation |
| **9. Hour-over-Hour Growth** | *Where does the evening rush start?* | **CTE + `LAG()`** |
| **10. Zone Revenue Concentration** | *Can we focus on a few zones? (Pareto test)* | **Running `SUM() OVER`** |
| **11. Rating Band vs Fare** | *Do better-rated drivers earn more?* | **`CASE WHEN` banding** |

### 3. Visual EDA (`UberTripAnalysis.ipynb`)
Python-driven exploration of cleaned trip data including:
* **Heatmaps:** Hour × Day-of-Week demand matrix to visualize peak traffic windows.
* **Vehicle Revenue Charts:** Side-by-side comparison of total and per-km revenue.
* **Distribution Plots:** Fare and distance histograms to detect outliers and skew.
* **Pickup Location Bar Charts:** Top revenue zones ranked horizontally.

### 4. Predictive Fare Modeling (`UberTripAnalysis.ipynb`)
Predictive modeling implemented via Scikit-learn to forecast trip fare amounts and validate non-linear fare drivers:
* **Feature Engineering & Preprocessing:** Label encoding on categorical variables (`Vehicle_Type`, `Pickup_Location`) alongside continuous features (`Trip_Distance_km`, `Hour`, `Duration_Minutes`).
* **Model Implementation:** `RandomForestRegressor` trained on an 80/20 train-test split (`test_size=0.2, random_state=42`) to capture non-linear distance and time-of-day interactions.
* **Evaluation & Metric Tracking:** Quantified predictive accuracy using **Root Mean Squared Error (RMSE)** and **$R^2$ Score** ($R^2$ benchmarked against baseline linear fare expectations), confirming high fidelity between model predictions and realized trip revenues.

---

## Visual Deep-Dive & KPI Handbook

*Every figure below is generated from `data/Uber_Cleaned_data.csv` (35,000 trips). Figures are in ₹ (INR) — the dataset uses Indian payment methods including UPI.*

### KPI Handbook — what each headline number means

| KPI | Value | Definition |
|---|---|---|
| Total Trips | **35,000** | Cleaned trip rows after deduplication |
| Total Revenue | **₹13.54M (₹1,35,44,703)** | Sum of trip fares |
| Avg Fare | **₹387** | Mean fare per trip |
| Avg Distance | **17.45 km** | Mean trip distance |
| Avg Duration | **45.5 min** | Mean trip duration |
| Avg Rating | **4.32** | Mean driver rating |

### Chart-by-chart walkthrough

**Trips by Hour of Day** — the money chart: demand is near zero at 3 AM (~350 trips) and explodes to 4,053 trips at 6 PM. The 5–7 PM window carries 31.2% of all demand. Critically, `LAG()` growth analysis shows demand *accelerates* at 5 PM (+138%) an hour before the 6 PM volume peak — so driver incentives must fire at ~4:30 PM, not at the peak itself.

![Hourly Demand](image/uber_hourly_demand.png)

**Vehicle Revenue** — total vs per-tier revenue split: the premium tier concentrates revenue per trip while economy tiers concentrate volume. Fleet-growth capital belongs on the tier with the best revenue-per-trip, not the most trips.

![Vehicle Revenue](image/uber_vehicle_revenue.png)

**Airport Share** — airport trips are 39.6% of volume but 54.8% of revenue: the airport corridor is the highest-yield segment and deserves dedicated positioning.

![Airport Share](image/uber_airport_share.png)

**Pickup Zone Pareto** — 5 pickup zones ranked: a small number of zones drive the majority of trips and revenue. Positioning supply on the top zones covers most demand with least deadheading.

![Zone Pareto](image/uber_zone_pareto.png)

**Rating vs Fare** — the correlation matrix confirms ratings fall slightly with distance (-0.13) and barely move with fare (-0.09): the rating gap is about trip length (long-trip fatigue), not driver quality — so rating-based driver penalties would punish the wrong behavior.

![Rating vs Fare](image/uber_rating_vs_fare.png)

**Correlation Heatmap** — the EDA backbone: fare tracks distance and duration; hour drives demand volume; ratings are largely orthogonal to money variables.

---

## Core Analytical Insights

![Correlation Heatmap](image/Ubertrip_heatmap.png)
*The correlation matrix independently confirms Q4: driver rating correlates **-0.13** with trip distance and only **-0.09** with fare. Longer trips rate worse — the rating gap is about trip length, not driver quality.*

### Per-chart visuals
The interactive Power BI dashboard sits in `powerbi/UberTrip_Dashboard.pbix` and the Excel summary in `excel_analysis/`. The PNGs below surface the same charts in a viewable form for the README.

| Hourly Demand | Vehicle Revenue | Airport Trip Share |
|:--|:--|:--|
| ![](image/uber_hourly_demand.png) | ![](image/uber_vehicle_revenue.png) | ![](image/uber_airport_share.png) |

| Zone Pareto | Fare by Driver Rating |
|:--|:--|
| ![](image/uber_zone_pareto.png) | ![](image/uber_rating_vs_fare.png) |

### 1. Peak Demand Windows
The hourly demand heatmap shows a clear **evening peak**: the busiest hours are **6 PM (4,053 trips), 5 PM (3,467), and 7 PM (3,411)** — a textbook after-work commute surge. Late-night fares are *not* meaningfully elevated in this data (≈2% above average), so the genuine operational signal is the evening volume spike, not a late-night premium.

Adding a `LAG()` comparison sharpens this into something actionable: **the surge begins at
5 PM, not 6 PM.** Peak *volume* and peak *growth* are different hours, and only the
hour-over-hour view reveals it. Incentives launched at 6 PM arrive an hour late.

### 2. Vehicle Category Revenue Efficiency
* **Revenue-per-km by tier** (total fare ÷ total distance, matching §3 of the SQL): Uber Black **₹40.06**, UberXL ₹26.65, Comfort ₹25.31, UberX ₹20.30, Uber Pool ₹14.08. Premium (Black) earns ≈ **2.0× UberX** and **2.8× Uber Pool**.
* **But total revenue tells a different story:** UberX leads total revenue (**₹49.1L**) on sheer volume, while Black is high-margin-per-km but lower volume — a classic premium-vs-volume trade-off.

### 3. Airport Trip Premium
* Airport trips are **39.6%** of bookings (high, reflecting the synthetic data) and carry a real fare premium: **₹535.77 vs ₹289.40** for city trips (≈ **1.85×**). They account for **54.8% of total revenue** — supporting a dedicated airport dispatch strategy.

### 4. Weekend Fare Behavior
* Weekend vs weekday average fare is **₹389.34 vs ₹386.05** — a **<1% difference**. Honest read: there is *no* material weekend fare effect in this dataset, so a weekend-specific pricing rule isn't justified by the data.

### 5. The Driver-Rating Trap
Ranked by average fare, the *worst*-rated drivers look like the best earners
(₹419.18 for <4.0 vs ₹364.24 for 4.8–5.0). Acting on that would be a mistake.
Controlling for distance dissolves the effect entirely — **fare-per-km is ₹22.06–22.41
across every rating band**. The real signal is that long trips (18.9 km avg for the
lowest band) attract worse ratings.

---

## Business Recommendations

1. **Demand-Based Surge Pricing:** Focus fare multipliers on the **5–7 PM evening peak**, where trip volume is genuinely highest — this is the strongest, data-backed lever. Launch incentives by **4:30 PM**, since growth accelerates an hour before volume peaks.
2. **Airport Fleet Allocation:** With airport trips earning ~1.85× the average fare and contributing 54.8% of revenue, pre-position premium/SUV drivers for airport demand.
3. **Premium-vs-Volume Mix:** Keep UberX as the volume/revenue backbone while protecting Uber Black's 2.8× per-km margin — don't over-discount the premium tier.
4. **Long-Trip Experience Review:** Investigate why trips over ~18 km rate poorly, rather than flagging the drivers who happen to take them.
5. **Maintain City-Wide Coverage:** With 4 of 5 zones needed to reach 80% of revenue, do not concentrate supply in a handful of areas.

> *Note: an earlier draft recommended a weekend surcharge and late-night surge — the data shows neither effect is real here, so those were removed. Knowing which recommendations the data does **not** support is part of the analysis.*
