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

**I answer business questions with data — including the ones where the answer is "don't do it."**

Two end-to-end analytics projects covering **43,000 records**: a supply-chain P&L and
fulfilment audit, and a ride-demand and pricing analysis. Every figure below is
reproducible from the committed SQL and Python in this repository.

As a **B.Sc IT graduate** and **aspiring Data Analyst**, I specialize in translating complex datasets into clean, reliable, and actionable business insights.

---

## 📈 Portfolio at a Glance

| Project | Scale | Stack | Headline Result |
|---------|-------|-------|-----------------|
| **Supply Chain Performance** | 7,991 orders · 47 SKUs | Python · SQL · Excel VBA | $82.7M revenue / $30.9M profit analysed; late delivery proven systemic, not warehouse-specific |
| **Uber Trip Demand** | 35,000 trips | MySQL · Python · Power BI | 5–7 PM carries 31.2% of demand; airport trips are 39.6% of volume but 54.8% of revenue |

---

## 🎯 Business Questions I Answered

If an interviewer asks one of these, the query and the number are already in this repo.

| Business Question | Finding | Decision It Drives |
|:--|:--|:--|
| Half our orders are late — which warehouse is at fault? | **None.** Only **0.08%** of delivery-time variance is between warehouses; all six have 2.82–2.88 day spread. | Fix upstream scheduling, not a facility — a per-site project would fix nothing |
| Isn't our biggest warehouse the worst offender? | **No — a volume illusion.** It causes 31.9% of late orders but handles 31.4% of all orders. | Always normalise counts by volume before ranking anything |
| Are discounts eating our margin? Should we cap them? | **No.** Orders at 20%+ discount return **38.28%** margin — *higher* than the 5–10% band. | Don't cap discounts; you'd lose revenue protecting nothing |
| When should a ride-hailing firm surge-price? | **5–7 PM carries 31.2% of demand** in 3 of 24 hours — and the surge *starts* at 5 PM, not 6 PM when volume peaks. | Launch driver incentives by 4:30 PM, an hour ahead of peak |
| Do higher-rated drivers earn more per trip? | **No, and the obvious read is backwards.** Low-rated drivers show higher fares — but only because they drive longer trips. Fare-per-km is flat at ₹22.06–22.41. | Investigate long-trip rider experience; don't penalise drivers |
| Can we focus on just our top revenue zones? | **No.** It takes **4 of 5 zones** to reach 80% of revenue. | Keep coverage city-wide — the 80/20 assumption fails here |

**Six of these; four say "don't act."** Knowing where *not* to spend is the part that
saves budget.

---

## 🛠️ Core Analytical Skills & Tools

| Category | Technologies & Libraries | Key Methodologies |
| :--- | :--- | :--- |
| **Languages** | Python, SQL (MySQL / PostgreSQL), HTML/CSS | Exploratory Data Analysis (EDA), Statistical Analysis |
| **Data Libraries** | Pandas, NumPy, Scikit-Learn, Matplotlib, Seaborn | Data Cleaning, Feature Engineering, Outlier Detection |
| **BI & Visualization** | Power BI, Advanced Microsoft Excel (VBA, Power Query, Pivots) | Interactive Dashboard Design, Executive KPI Reporting |
| **Development Workflow** | Jupyter Notebooks, Git & GitHub, PowerShell / Bash | Automation Scripting, ETL Pipeline Construction |
| **SQL Techniques** | CTEs, `LAG()`, `RANK()`, `ROW_NUMBER()`, running `SUM() OVER`, `STDDEV_SAMP` | Cohort Banding, Pareto Analysis, Trend Detection |

---

## 📊 Featured Analytical Projects

### 1. 📦 [Inventory & Logistics Performance Analytics](./supply-chain-performance-analysis/)

![Supply Chain Dashboard](./supply-chain-performance-analysis/image/Supplychain_Dashboard_screenshot.png)

*An end-to-end operational analytics project featuring a Python data cleaning pipeline, custom SQL metrics, and an automated, fully interactive 10-chart Excel dashboard.*
* **Business Challenge:** Half of all orders miss the 5-day delivery target, with $41.0M of revenue exposed — and leadership needs to know whether to invest in a specific warehouse or the network.
* **Tech Stack:** Python (Pandas, openpyxl), SQL (MySQL — CTEs, `STDDEV`, `LAG`, window functions), Microsoft Excel (VBA, Macros, Pivot Tables).
* **Key Achievements:**
  * **Disproved the obvious answer.** Ranking warehouses by late-order count blames the largest site; variance decomposition shows only **0.08%** of delivery-time variance is between warehouses. Prevented a misdirected improvement programme.
  * Cleaned and processed raw transactional data, generating dynamic metrics like **Delivery Days**, **Order-to-Ship Days**, and **Profit Margins** ($82.7M gross revenue / $30.9M profit across 7,991 orders).
  * Implemented an automated Excel workbook generator (`build_excel_dashboard.py`) using `openpyxl` with dynamic dropdown selectors, date-range inputs, and custom formula-driven pivot tables.
  * Designed an executive **Summary** sheet containing KPI cards, performance grids, and narrative insights on fulfilment performance.
  * Used **ABC Classification** to segment the 47-SKU catalogue by revenue contribution (A-items = 78.7% of revenue) — with an honest read that this catalogue shows only moderate, not textbook 80/20, concentration.
  * Shipped a reproducible Python pipeline (`src/data_cleaning.py`, `src/analytics.py`, `src/build_excel_dashboard.py`) so every quoted figure regenerates from the raw data.

### 2. 🚖 [Ride Demand Forecasting & Revenue Analytics](./uber-trip-demand-analysis/)

![Uber Power BI Dashboard](./uber-trip-demand-analysis/image/PowerBi_Dashboard.png)

*A comprehensive revenue and behavioral analysis of ride-sharing transactions using SQL data warehousing, Python visualization, and Excel dashboarding.*
* **Business Challenge:** Identifying when to surge-price, where to position premium vehicles, and which fleet tier to grow across 35,000 trips.
* **Tech Stack:** MySQL (window functions, CTEs, `LAG`, running totals), Python (Seaborn, Matplotlib), Advanced Excel, Power BI.
* **Key Achievements:**
  * Used `LAG()` to separate peak *volume* from peak *growth* — demand accelerates at **5 PM (+138%)**, an hour before the 6 PM volume peak, moving the incentive trigger an hour earlier.
  * Caught a confounded metric: lower-rated drivers appear to earn more, but the effect vanishes once trip distance is controlled for (**fare-per-km flat at ₹22.06–22.41**).
  * Quantified that **airport trips are 39.6% of volume but 54.8% of revenue** (₹535.77 vs ₹289.40 avg fare).
  * Built a MySQL schema over 35,000 records with `ROW_NUMBER()` deduplication and null validation.
  * Conducted vehicle-category analysis measuring revenue per ride and revenue-to-distance efficiency (Uber Black ₹40.06/km vs Uber Pool ₹14.08/km).
  * Reported three **negative findings** (no weekend fare effect, no seasonality, no zone concentration) that removed unjustified recommendations from an earlier draft.

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