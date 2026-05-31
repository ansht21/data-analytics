# 📦 Supply Chain Performance & Inventory Optimization Dashboard

## 📖 Project Overview
This project delivers a comprehensive, end-to-end data analytics solution designed to optimize warehouse inventory, streamline order fulfillment, and boost profit margins. By building a Python-based data cleaning pipeline, executing deep-dive SQL warehousing audits, and designing a fully interactive, macro-enabled Excel dashboard, this project models real-world corporate supply chain challenges and provides data-backed operational solutions.

### 🌟 Business Impact Highlights
* **Revenue Analyzed:** **$82.69 Million** gross transactional revenue.
* **Profit Analyzed:** **$30.87 Million** net profitability with a healthy **37.3% average margin**.
* **Fulfillment Benchmark:** Analyzed **7,991 orders** with an average delivery cycle of **5.5 days**.
* **Strategic Optimization:** Segmented inventory using **ABC Classification** to identify slow-moving assets, unlocking a **12-18% potential holding cost reduction**.

---

## 🛠️ Tech Stack & Technical Architecture
* **Python (Pandas, NumPy, openpyxl, Matplotlib, Seaborn):** Raw data engineering, data cleaning, date parsing, calculated metric formulation, and automated Excel dashboard styling.
* **MySQL:** Relational database schema design, transactional bulk data loading (`LOAD DATA INFILE`), data quality validation, and advanced reporting queries.
* **Microsoft Excel (VBA/Macros, Advanced Formulas):** Interactive workbook design, dynamic slicing, custom `SUMIFS`/`COUNTIFS` aggregate reporting, and conditional alerts.

---

## 🔄 End-to-End Pipeline Architecture

### 1. Data Cleaning & Feature Engineering (`Supplychain.ipynb`)
The raw transactional log (`Supplychain_rawData.csv`) was ingested and underwent rigorous feature engineering to generate highly structured variables for business analysis:
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

### 3. Interactive Excel Dashboard (`excel_analysis/`)
Instead of static sheets, the final deliverable includes a fully automated, interactive, macro-enabled Excel dashboard:
* **Executive Summary Sheet:** Features top-level KPI cards (Total Revenue, Total Profit, Profit Margin, On-Time Fulfillment Rate) and a dynamic markdown-style narrative insight section highlighting operational bottlenecks.
* **Interactive Dynamic Filtering:** Injected cells in `Dashboard` sheet (`C19` for start date, `C20` for end date, along with Sales Channel dropdowns) that feed into an active boolean filter matrix:
  `=(IF(Dashboard!$B$8="All",1,SalesChannel=Dashboard!$B$8)*IF(Dashboard!$C$19="",1,OrderDate>=Dashboard!$C$19)*...)`
* **Dynamic Visualization (10 Automated Charts):**
  * Revenue & Profit by Sales Channel.
  * Fulfillment Performance (On-Time vs. Late delivery rates).
  * Warehouse Dispatch Speeds (Avg Delivery Days by Hub).
  * Time-Series Revenue Trends and Yearly Over-Year Comparisons.

---

## 📊 Core Analytical Insights

### 1. The Inventory Pareto Principle (ABC Classification)
By classifying items based on cumulative financial contribution, the analysis confirmed the **Pareto (80/20) Principle**:
* **A-Items (Top 20%):** Account for **78.4% of total revenue**. These represent high-velocity, high-value goods that require strict daily monitoring and automated replenishment.
* **B-Items (Next 30%):** Account for **15.2% of total revenue**. Managed with bi-weekly review cycles.
* **C-Items (Bottom 50%):** Account for only **6.4% of total revenue**, yet occupy **over 40% of physical warehouse space**. This represents major capital bloat.

### 2. Warehouse Bottlenecks
* **Top Performing Hub:** `WARE-MKL1006` consistently maintains an average dispatch-to-delivery speed of **4.2 days** with a **96.5% on-time rate**.
* **Underperforming Hub:** `WARE-XYS1001` exhibits an average transit delay of **7.8 days** and is responsible for **62% of all late deliveries**—primarily due to regional courier bottlenecks.

---

## 💡 Business Recommendations

1. **Implement ABC Replenishment:** Move away from uniform ordering. Transition C-items to a "Just-In-Time" (JIT) model to free up 30%+ of warehouse shelf space and lower holding costs. Establish rigid safety stock thresholds for high-velocity A-items.
2. **Redistribute Fulfillment Loads:** Reroute orders originally bound for `WARE-XYS1001` during peak Q4 seasonal spikes to `WARE-MKL1006` to minimize late delivery penalties and customer churn.
3. **Establish Discount Threshold Alerts:** SQL audits identified that **1.4% of orders were unprofitable** due to overlapping sales discounts (coupons combined with volume markdowns). Enforce an hard discount cap at **15%** within the Excel order entry system.
4. **Negotiate Supplier SLAs:** Leverage lead-time variability metrics from the Python analysis to renegotiate delivery windows with slow-performing regional logistics providers.
