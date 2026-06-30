# 📦 Supply Chain Performance & Inventory Optimization Dashboard

## 🎯 Business Purpose & Impact
> **Why I built this:** Companies don't hire analysts to make charts — they hire people who can answer *"where are we making or losing money, and what should we do about it?"* This project proves I can take **7,991 raw order records ($82.7M revenue)** and turn them into **profit-and-loss decisions**.

**The 3 business questions this project answers:**

| Question | Finding (from the data) | Business decision it drives |
| :--- | :--- | :--- |
| 💰 **Which channel makes us the most money?** | **In-Store leads** at $34.0M revenue / **$12.7M profit (41%)**, ahead of Online ($24.6M), Distributor ($14.8M), Wholesale ($9.2M). | Concentrate sales investment & inventory in the highest-return channels. |
| ✅ **Are discounts eating our margin?** | Discounts range **5%–40%** (avg 11.6%), yet margin holds at **37.4%** with **zero loss-making orders**. | Add a discount guardrail to **protect margin as volume grows**. |
| 📦 **Where is revenue concentrated?** | **35 of 47 products drive 78.7% of revenue.** | Stock high-value items tightly; run the long tail lean → **lower holding cost, same revenue**. |

> 💡 **My edge — I read the data critically, not just optimistically.** While analysing delivery times I noticed they're *uniformly distributed* (≈800 orders at every value 1–10 days), a sign the delivery dates are synthetic. So instead of overselling a fake "on-time" crisis, I lead with the **channel-profitability and margin findings that the data genuinely supports.** Knowing which insights to *trust* is the business judgment companies pay for.

---

## 📖 Project Overview
This project delivers a comprehensive, end-to-end data analytics solution designed to optimize warehouse inventory, streamline order fulfillment, and boost profit margins. By building a Python-based data cleaning pipeline, executing deep-dive SQL warehousing audits, and designing a fully interactive, macro-enabled Excel dashboard, this project models real-world corporate supply chain challenges and provides data-backed operational solutions.

### 🌟 Business Impact Highlights
*All figures are reproducible — run `python src/analytics.py` to regenerate `outputs/kpi_summary.json`.*
* **Revenue Analyzed:** **$82.69 Million** gross transactional revenue.
* **Profit Analyzed:** **$30.87 Million** net profitability with a healthy **37.4% average margin**.
* **Fulfillment Benchmark:** Analyzed **7,991 orders** with an average delivery cycle of **5.5 days** (range 1–10 days).
* **Fulfillment Gap:** Only **50.5%** of orders met the **5-day delivery target** — **3,953 late orders**, the single clearest operational opportunity.

---

## 🛠️ Tech Stack & Technical Architecture
* **Python (Pandas, NumPy, openpyxl, Matplotlib, Seaborn):** Raw data engineering, data cleaning, date parsing, calculated metric formulation, and automated Excel dashboard styling.
* **MySQL:** Relational database schema design, transactional bulk data loading (`LOAD DATA INFILE`), data quality validation, and advanced reporting queries.
* **Microsoft Excel (VBA/Macros, Advanced Formulas):** Interactive workbook design, dynamic slicing, custom `SUMIFS`/`COUNTIFS` aggregate reporting, and conditional alerts.

---

## 🔄 End-to-End Pipeline Architecture

### 1. Data Cleaning & Feature Engineering (`src/data_cleaning.py` · `Supplychain.ipynb`)
The raw transactional log (`Supplychain_rawData.csv`) is ingested by `src/data_cleaning.py`, which performs feature engineering to generate structured variables for business analysis and writes `data/Cleaned_Supplychain_Data.csv`:
* **Header Standardization:** Stripped whitespaces and mapped columns using clean snake_case headers (e.g., `Order_Quantity`, `Unit_Cost`, `Unit_Price`).
* **Data Cleansing:** Removed localized currency symbols (`$`) and formatting commas, casting numerical strings to `float64` for calculation accuracy.
* **Fulfillment Metrics:**
  * `delivery_days` = `DeliveryDate - ShipDate` *(Avg: 5.5 days; Min: 1 day; Max: 10 days)*.
  * `order_to_ship_days` = `ShipDate - OrderDate` *(Measures warehouse dispatch response times)*.
  * `procure_to_order_days` = `OrderDate - ProcuredDate` *(Measures procurement lead times)*.
* **Financial Formulas:**
  * `revenue` = `Order_Quantity * Unit_Price`
  * `total_cost` = `Order_Quantity * Unit_Cost`
  * `profit` = `revenue - total_cost`

### 2. Relational SQL Warehousing (`sql_queries/`)
Using MySQL, the engineered transaction data was schema-mapped and uploaded for high-throughput reporting:
* **`01_database_setup.sql`:** Handles schema generation, enforces data integrity constraints, and conducts optimized bulk-data loads of clean transactional data.
* **`02_sales_analysis.sql`:** Aggregates multi-dimensional reports including:
  * **Data Quality Audit:** Measures and reports null dates across the workflow.
  * **Sales Channel Deep-Dive:** Tracks gross revenue, discount impacts, net revenue, and margin percentages.
  * **Warehouse Efficiency Breakdown:** Ranks fulfillment hubs by average dispatch and transit speed.
  * **Profit Margin Integrity Audit:** Detects individual transactions that were sold at a loss due to over-discounting.

### 3. Interactive Excel Dashboard (`src/build_excel_dashboard.py` → `excel_analysis/`)
`src/build_excel_dashboard.py` reads the cleaned data and generates a styled,
multi-sheet workbook (`Supplychain_Dashboard.xlsx`) with `openpyxl`:
* **Executive Dashboard Sheet:** Top-level KPI cards (Total Revenue, Total Profit, Profit Margin, Order Count, Avg Delivery, On-Time %).
* **ChartData Sheet:** Formula-free aggregated pivots (revenue by channel, avg delivery days by warehouse, monthly revenue) driving the charts.
* **Native Charts:** Revenue by Sales Channel (pie), Avg Delivery Days by Warehouse (column), and Monthly Revenue Trend (line).

> A separate macro-enabled workbook (`Supplychain_Data_Dashboard.xlsm`) with
> dropdown/date-range slicers is also included as a hand-built interactive deliverable.

### 4. Power BI Model (`powerbi/`)
A Power BI report built on the cleaned CSV, with DAX measures and a 3-page layout
(Executive Overview, Fulfillment, Profitability). See [`powerbi/README.md`](./powerbi/README.md).

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
python src/data_cleaning.py        # -> data/Cleaned_Supplychain_Data.csv
python src/analytics.py            # -> outputs/kpi_summary.json, abc_classification.csv, warehouse_performance.csv
python src/build_excel_dashboard.py # -> excel_analysis/Supplychain_Dashboard.xlsx
```

---

## 📊 Core Analytical Insights
*Generated by `src/analytics.py`; see `outputs/` for the raw tables.*

### 1. Inventory Concentration (ABC Classification)
Classifying the **47 distinct products** by cumulative revenue contribution shows a
**moderate** concentration rather than a strict 80/20 split:
* **A-Items:** 35 products (74.5%) → **78.7%** of revenue — high-velocity goods needing tight replenishment control.
* **B-Items:** 8 products (17.0%) → **14.7%** of revenue — bi-weekly review cycle.
* **C-Items:** 4 products (8.5%) → **6.5%** of revenue — candidates for Just-In-Time stocking.

> *Honest caveat:* with only 47 SKUs and fairly uniform order values, this catalogue
> does **not** exhibit a textbook Pareto curve. The takeaway is that revenue is
> broadly distributed, so blanket "cut the long tail" advice would be misguided here.

### 2. Fulfillment Performance
* **On-time rate (≤5-day target): 50.5%** — **3,953 of 7,991 orders ran late.**
* Delivery speed is **remarkably uniform across warehouses** (avg **5.35–5.59 days**); `WARE-MKL1006` is marginally fastest and `WARE-XYS1001` slowest, but the spread is <0.3 days. There is **no single bottleneck hub** — the lateness is systemic, not localized.

### 3. Profitability
* Margins are healthy and consistent (**37.4% average**); **zero orders were sold at a loss**, indicating disciplined pricing even with discounts applied.

---

## 💡 Business Recommendations

1. **Attack the systemic delivery gap, not a single hub.** Since all warehouses average ~5.5 days and ~half of orders miss the 5-day target, the fix is a network-wide carrier/SLA review rather than rerouting to one "good" hub.
2. **Tier replenishment by the A/B/C split.** The 35 A-items drive ~79% of revenue — prioritise their stock availability; review the 4 C-items for JIT ordering to trim holding cost.
3. **Protect the healthy margin.** With no loss-making orders today, enforce a discount cap in the order-entry workflow to keep it that way as volumes grow.
4. **Tighten the delivery SLA target.** Re-baselining "on-time" and negotiating carrier windows could move the 50.5% rate materially — the biggest lever in the dataset.
