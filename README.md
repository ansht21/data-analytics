<div align="center">

# 📊 Data Analytics Portfolio
### Turning Raw Data into Business Strategy

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Excel](https://img.shields.io/badge/Excel-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

</div>

---

Welcome to my Data Analytics Projects repository! This repository showcases end-to-end data lifecycle projects—ranging from automated ETL pipelines and SQL data warehousing to exploratory analysis and interactive executive dashboards. 

As a **B.Sc IT graduate** and **aspiring Data Analyst**, I specialize in translating complex datasets into clean, reliable, and actionable business insights.

---

## 📈 Portfolio at a Glance

| Project | Scale | Stack | Headline Result |
|---------|-------|-------|-----------------|
| **Supply Chain Performance** | 47 SKUs | Python · SQL · Excel VBA | $82.6M revenue / $30.8M profit analysed; A-items = 78.7% of revenue |
| **Uber Trip Demand** | 35,000 trips | MySQL · Python · Power BI | Identified 5–7 PM surge window; revenue-per-km efficiency by vehicle class |

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

![Supply Chain Dashboard](./supply-chain-performance-analysis/image/Supplychain%20Dashboard_screenshot.png)

*An end-to-end operational analytics project featuring a Python data cleaning pipeline, custom SQL metrics, and an automated, fully interactive 10-chart Excel dashboard.*
* **Business Challenge:** Inefficient stock management leading to bloated holding costs and high supplier lead-time variability.
* **Tech Stack:** Python (Pandas, openpyxl), SQL (MySQL), Microsoft Excel (VBA, Macros, Pivot Tables).
* **Key Achievements:**
  * Cleaned and processed raw transactional data, generating dynamic metrics like **Delivery Days**, **Order-to-Ship Days**, and **Profit Margins** ($82.6M total revenue / $30.8M total profit).
  * Implemented an automated Excel workbook generator (`build_excel_dashboard.py`) using `openpyxl` with dynamic dropdown selectors, date-range inputs, and custom formula-driven pivot tables.
  * Designed an executive **Summary** sheet containing KPI cards, performance grids, and narrative insights rating warehouse efficiency (identifying bottlenecks and safety stock recommendations).
  * Used **ABC Classification** to segment the 47-SKU catalogue by revenue contribution (A-items = 78.7% of revenue) and recommend tiered stocking levels — with an honest read that this catalogue shows only moderate, not textbook 80/20, concentration.
  * Shipped a reproducible Python pipeline (`src/data_cleaning.py`, `src/analytics.py`, `src/build_excel_dashboard.py`) so every quoted figure regenerates from the raw data.

### 2. 🚖 [Ride Demand Forecasting & Revenue Analytics](./uber-trip-demand-analysis/)

![Uber Power BI Dashboard](./uber-trip-demand-analysis/image/PowerBi_Dashboard.png)

*A comprehensive revenue and behavioral analysis of ride-sharing transactions using SQL data warehousing, Python visualization, and Excel dashboarding.*
* **Business Challenge:** Identifying key revenue drivers, peak operational demand windows, and efficiency improvements across different vehicle categories.
* **Tech Stack:** MySQL (Window functions, CTEs), Python (Seaborn, Matplotlib), Advanced Excel.
* **Key Achievements:**
  * Built a MySQL database schema and handled 35,000 trip records, implementing robust deduplication using `ROW_NUMBER()` window functions and subqueries.
  * Extracted trip characteristics (peak times, airport trip percentages, and weekend vs. weekday fare variations).
  * Conducted vehicle-category analysis to measure revenue per ride and revenue-to-distance efficiency.
  * Provided operational recommendations including 5-7 PM evening surge windows and localized premium vehicle allocation.

---

## 📂 Repository Architecture

Each directory is fully self-contained, including its own documentation, SQL scripts, raw/cleaned datasets, and Jupyter analysis files:

```bash
data-analytics-projects/
│
├── 📦 supply-chain-performance-analysis/     # Operational efficiency & inventory dashboards
│   ├── src/                                  # Reproducible Python pipeline (clean, analytics, excel)
│   ├── data/                                 # Raw & processed CSV datasets (git-tracked)
│   ├── outputs/                              # Generated KPI summary & analysis tables
│   ├── excel_analysis/                       # Generated + interactive Excel dashboards
│   ├── powerbi/                              # Power BI model guide (DAX measures, layout)
│   ├── sql_queries/                          # Database schemas & analytical queries (.sql)
│   ├── image/                                # Dashboard screenshots & visual highlights
│   ├── requirements.txt                      # Python dependencies
│   ├── Supplychain.ipynb                     # Python EDA & feature engineering notebook
│   └── README.md                             # Detailed project report and insights
│
├── 🚖 uber-trip-demand-analysis/             # Ride-sharing demand & fare analytics
│   ├── data/                                 # Datasets & source structures
│   ├── excel_analysis/                       # Excel pivot table summaries
│   ├── sql_queries/                          # MySQL data-cleaning and analytics scripts (.sql)
│   ├── powerbi/                              # Power BI report (.pbix)
│   ├── image/                                # Visual analysis plots & demand curves
│   ├── UberTripAnalysis.ipynb                # Interactive Python behavioral analytics
│   └── README.md                             # Complete project brief and recommendations
│
└── README.md                                 # Main portfolio lander (this file)
```

---

## 📬 Contact & Collaboration

I am actively seeking entry-level **Data Analyst**, **Business Intelligence Analyst**, or **Data Engineer** roles where I can help teams turn complex data into clean, business-boosting decisions.

<div align="center">

[![Portfolio](https://img.shields.io/badge/Portfolio-ansh--thakur.netlify.app-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://ansh-thakur.netlify.app/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ansh-thakur-5407192b4/)
[![Email](https://img.shields.io/badge/Email-ansht1194@gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:ansht1194@gmail.com)

</div>

Feel free to browse my code, download the interactive Excel dashboards to explore their dynamic filters, or connect with me on LinkedIn!
