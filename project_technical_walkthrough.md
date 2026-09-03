# Project Technical Deep-Dive: Supply Chain Inventory Optimization

This document serves as your "cheat sheet" to explain how this project was built—from raw data to business insights. Use this to prepare for interviews or to walk a recruiter through your analytical process.

---

## 1. The "Why" (Business Context)
* **Problem:** Inefficient inventory management leads to bloated storage costs (holding costs) and lost sales due to stockouts.
* **Goal:** Use data to identify which items drive the most revenue vs. which items just take up space, and identify why deliveries were late.

## 2. The Data Pipeline (How it was created)

### Phase 1: Data Preparation (Python)
* **Tools:** `Pandas`, `openpyxl`.
* **Action:** I started with a raw, messy CSV (`Supplychain_rawData.csv`).
* **Steps:**
    1. **Cleaning:** I removed currency symbols (`$`) and commas from price columns so Python could do math on them.
    2. **Standardization:** I renamed headers to "snake_case" (e.g., `Unit_Price`) to make them SQL-friendly.
    3. **Feature Engineering:** I created new columns that didn't exist in the raw data, including realised net `revenue` (after discount), `profit` (`net revenue - cost`), and `delivery_days` (`DeliveryDate - ShipDate`).

### Phase 2: Data Warehousing (SQL)
* **Tools:** `MySQL`.
* **Action:** I moved the cleaned data into a database.
* **Steps:**
    1. **Schema Design:** I defined data types for every column (e.g., `INT` for quantity, `DECIMAL` for currency) to ensure data integrity.
    2. **Analytical Queries:** I didn't just select the data; I asked the data questions.
        * *Example:* "Which warehouse is the bottleneck?" I grouped by warehouse ID and calculated average delivery delays.
        * *Example:* "What is my Pareto split?" I used calculations to categorize items into A, B, and C groups based on their revenue contribution.

### Phase 3: Visualization & Dashboarding (Excel)
* **Tools:** `Excel`, `openpyxl`.
* **Action:** Created an interactive dashboard.
* **Steps:**
    1. **Dashboard generation:** I generate a consistent executive dashboard with KPI cards, native Excel charts, and chart-ready aggregates.
    2. **Auditability:** The workbook includes the chart source data so results can be reviewed against the cleaned pipeline output.

---

## 3. The "Elevator Pitch" for Interviews
When someone asks, "Tell me about this project," use this structure:

> "For my Supply Chain project, I built a pipeline to help a company optimize inventory. I used Python to clean a messy transactional dataset and calculate consistent net revenue, profit margins, and fulfillment speed. I loaded the cleaned output into MySQL for a reproducible deep-dive and used ABC classification to show that revenue is broadly distributed rather than a textbook 80/20 split. Finally, I built an executive Excel dashboard with KPI cards and native charts, which showed late delivery is systemic across warehouses rather than caused by one facility."

---

## 4. Key Interview Questions to Prepare For
* **"How did you handle missing data or outliers?"** (Mention the cleaning step in Python).
* **"Why did you use ABC classification?"** (Answer: To help management prioritize resources on the most profitable items).
* **"What was the biggest technical challenge?"** (Answer: Cleaning the raw string-formatted currency data and ensuring the Excel dynamic filters were correctly linked).
