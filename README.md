# 📊 Data Analytics Portfolio: Turning Raw Data into Business Strategy

Welcome to my Data Analytics Projects repository! This repository showcases end-to-end data lifecycle projects—ranging from automated ETL pipelines and SQL data warehousing to exploratory analysis and interactive executive dashboards. 

As a **B.Sc IT graduate** and **aspiring Data Analyst**, I specialize in translating complex datasets into clean, reliable, and actionable business insights.

---

## 🌐 Quick Links
* **Portfolio Website:** [ansh-thakur.netlify.app](https://ansh-thakur.netlify.app/)
* **LinkedIn:** [linkedin.com/in/ansh-thakur-5407192b4](https://www.linkedin.com/in/ansh-thakur-5407192b4/)
* **GitHub Profile:** [github.com/ansht120](https://github.com/ansht120)

---

## 🛠️ Core Analytical Skills & Tools

| Category | Technologies & Libraries | Key Methodologies |
| :--- | :--- | :--- |
| **Languages** | Python, SQL (MySQL / PostgreSQL), HTML/CSS | Exploratory Data Analysis (EDA), Statistical Analysis |
| **Data Libraries** | Pandas, NumPy, Scikit-Learn, Matplotlib, Seaborn | Data Cleaning, Feature Engineering, Outlier Detection |
| **BI & Visualization** | Power BI, Advanced Microsoft Excel (VBA, Power Query, Pivots) | Interactive Dashboard Design, Executive KPI Reporting |
| **Development Workflow** | Jupyter Notebooks, Git & GitHub, PowerShell / Bash | Automation Scripting, ETL Pipeline Construction |

---

## 📊 Featured Analytical Projects

### 1. 📦 [Inventory & Logistics Performance Analytics](./supply-chain-performance-analysis/)
*An end-to-end operational analytics project featuring a Python data cleaning pipeline, custom SQL metrics, and an automated, fully interactive 10-chart Excel dashboard.*
* **Business Challenge:** Inefficient stock management leading to bloated holding costs and high supplier lead-time variability.
* **Tech Stack:** Python (Pandas, openpyxl), SQL (MySQL), Microsoft Excel (VBA, Macros, Pivot Tables).
* **Key Achievements:**
  * Cleaned and processed raw transactional data, generating dynamic metrics like **Delivery Days**, **Order-to-Ship Days**, and **Profit Margins** ($82.6M total revenue / $30.8M total profit).
  * Implemented an automated Excel workbook generator (`build_excel_dashboard.py`) using `openpyxl` with dynamic dropdown selectors, date-range inputs, and custom formula-driven pivot tables.
  * Designed an executive **Summary** sheet containing KPI cards, performance grids, and narrative insights rating warehouse efficiency (identifying bottlenecks and safety stock recommendations).
  * Used **ABC Classification** to segment inventory, proving the Pareto principle (20% of products driving 80% of value) and recommending tiered stocking levels.

### 2. 🚖 [Ride Demand Forecasting & Revenue Analytics](./uber-trip-demand-analysis/)
*A comprehensive revenue and behavioral analysis of ride-sharing transactions using SQL data warehousing, Python visualization, and Excel dashboarding.*
* **Business Challenge:** Identifying key revenue drivers, peak operational demand windows, and efficiency improvements across different vehicle categories.
* **Tech Stack:** MySQL (Window functions, CTEs), Python (Seaborn, Matplotlib), Advanced Excel.
* **Key Achievements:**
  * Built a MySQL database schema and handled millions of trip records, implementing robust deduplication using `ROW_NUMBER()` window functions and subqueries.
  * Extracted trip characteristics (peak times, airport trip percentages, and weekend vs. weekday fare variations).
  * Conducted vehicle-category analysis to measure revenue per ride and revenue-to-distance efficiency.
  * Provided operational recommendations including demand-based surge pricing rules for weekends and localized premium vehicle allocation.

---

## 📂 Repository Architecture

Each directory is fully self-contained, including its own documentation, SQL scripts, raw/cleaned datasets, and Jupyter analysis files:

```bash
data-analytics-projects/
│
├── 📦 supply-chain-performance-analysis/     # Operational efficiency & inventory dashboards
│   ├── data/                                 # Raw & processed CSV datasets (git-tracked)
│   ├── excel_analysis/                       # Fully interactive dashboard (.xlsm workbook)
│   ├── sql_queries/                          # Standard database schemas & analytical queries (.sql)
│   ├── image/                                # Dashboard screenshots & visual highlights
│   ├── Supplychain.ipynb                     # Python EDA & feature engineering notebook
│   └── README.md                             # Detailed project report and insights
│
├── 🚖 uber-trip-demand-analysis/             # Ride-sharing demand & fare analytics
│   ├── data/                                 # Datasets & source structures
│   ├── excel_analysis/                       # Excel pivot table summaries
│   ├── sql_queries/                          # MySQL data-cleaning and analytics scripts (.sql)
│   ├── image/                                # Visual analysis plots & demand curves
│   ├── UberTripAnalysis.ipynb                # Interactive Python behavioral analytics
│   └── README.md                             # Complete project brief and recommendations
│
└── README.md                                 # Main portfolio lander (this file)
```

---

## 📬 Contact & Collaboration

I am actively seeking entry-level **Data Analyst**, **Business Intelligence Analyst**, or **Data Engineer** roles where I can help teams turn complex data into clean, business-boosting decisions.

* **Email:** [ansht1194@gmail.com](mailto:ansht1194@gmail.com)
* **LinkedIn:** [/in/ansh-thakur-5407192b4](https://www.linkedin.com/in/ansh-thakur-5407192b4/)
* **Portfolio Website:** [ansh-thakur.netlify.app](https://ansh-thakur.netlify.app/)

Feel free to browse my code, download the interactive Excel dashboards to explore their dynamic filters, or connect with me on LinkedIn!
