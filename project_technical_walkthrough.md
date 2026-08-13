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
    3. **Feature Engineering:** I created new columns that didn't exist in the raw data, like `profit` (`revenue - cost`) and `delivery_days` (`DeliveryDate - ShipDate`). These are the metrics that actually matter to a business.

### Phase 2: Data Warehousing (SQL)
* **Tools:** `MySQL`.
* **Action:** I moved the cleaned data into a database.
* **Steps:**
    1. **Schema Design:** I defined data types for every column (e.g., `INT` for quantity, `DECIMAL` for currency) to ensure data integrity.
    2. **Analytical Queries:** I didn't just select the data; I asked the data questions.
        * *Example:* "Which warehouse is the bottleneck?" I grouped by warehouse ID and calculated average delivery delays.
        * *Example:* "What is my Pareto split?" I used calculations to categorize items into A, B, and C groups based on their revenue contribution.

### Phase 3: Visualization & Dashboarding (Excel)
* **Tools:** `Excel (VBA/Macros)`.
* **Action:** Created an interactive dashboard.
* **Steps:**
    1. **Dynamic Filtering:** I used Excel formulas (like `SUMIFS`) linked to input cells so that when you change a date range or filter by "Sales Channel," the whole dashboard updates instantly.
    2. **Macro Automation:** I included VBA to handle repetitive formatting tasks, ensuring the dashboard looks clean every time new data is added.

---

## 3. The "Elevator Pitch" for Interviews
When someone asks, "Tell me about this project," use this structure:

> "For my Supply Chain project, I built a pipeline to help a company optimize inventory. I started by using Python to clean a messy transactional dataset and engineer new KPIs like profit margins and fulfillment speed. Then, I loaded that data into MySQL to perform a deep-dive analysis, where I used ABC classification to prove the Pareto principle—showing that 20% of their inventory was driving 80% of their revenue. Finally, I built an interactive Excel dashboard that allows stakeholders to filter data by date and channel, helping them identify which warehouse was causing 62% of their late deliveries."

---

## 4. Key Interview Questions to Prepare For
* **"How did you handle missing data or outliers?"** (Mention the cleaning step in Python).
* **"Why did you use ABC classification?"** (Answer: To help management prioritize resources on the most profitable items).
* **"What was the biggest technical challenge?"** (Answer: Cleaning the raw string-formatted currency data and ensuring the Excel dynamic filters were correctly linked).
