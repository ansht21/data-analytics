# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] - 2026-10-20
### Added
- Supply chain: `src/customer_concentration_analysis.py` (`outputs/customer_concentration_analysis.json`) — customer/store concentration risk (Herfindahl) and sales-team margin-spread mechanism test (README Q11/Q12)
- Uber: `src/surge_pricing_analysis.py` (`outputs/surge_pricing_analysis.json`) — genuine peak-hour price premium with airport-trip control, airport corridor price-vs-distance split, driver concentration and rating-distance confounder test (README Q9-Q12)
- Subscription retention: `src/churn_driver_analysis.py` (`outputs/churn_driver_analysis.json`) — tenure-band revenue-at-risk ranking, price-quartile non-monotonicity test, paperless-billing triple-control confounder test, corrected household-driver claims (README Q6-Q10)
- Root README: new Problem → Methodology → Finding → Decision rows for customer concentration, sales-team margin, genuine surge premium, non-price churn and the paperless-billing confounder test

### Changed
- Root README: supply chain, Uber and churn project sections now list the new analyses as key achievements
- Churn project: paperless-billing claim upgraded to a contract × tenure × payment-method triple control (old "negative findings" were under-tested)

## [2.1.0] - 2026-10-20
### Added
- Supply chain: `src/revenue_root_cause.py` — reproducible volume/price/mix root-cause analysis for "why did revenue stall?" (writes `outputs/revenue_root_cause.json`)
- Supply chain: `sql_queries/03_revenue_root_cause.sql` — 7 business-question queries in the existing BUSINESS QUESTION / Metric / Answer / Action style
- Supply chain README: new "Why Did Revenue Stall?" section with the full decomposition, plus Q9 and Q10 rows
- Root README: two new Problem → Methodology → Finding → Decision rows covering the revenue-stall root cause and the discount/delivery counterfactual

### Changed
- Root README: supply chain project now lists the root-cause decomposition as a key achievement
- Corrected stale currency and percentage figures in the supply chain section (₹3.63 cr exposure, 80.6% A-item revenue share) to match the committed pipeline output

## [2.0.0] - 2026-10-02
### Changed
- Modernized all Excel dashboards to executive purple card-based UI
- Updated all dashboard screenshots across repos
- Supply Chain dashboard: new interactive .xlsm with modern theme
- Churn dashboard: redesigned with executive insights panel

## [1.1.0] - 2026-09-30
### Added
- Root requirements.txt for unified dependency management
- Real-world 4-step analytics lifecycle framework in root README
- Statistical hypothesis testing details in project READMEs

## [1.0.0] - 2026-08-14
### Added
- Initial release with 3 complete analytics projects
- Supply Chain Performance Analysis with interactive Excel dashboard
- Uber Trip Demand Analysis with Power BI dashboard
- Subscription Retention Analytics with churn analysis
- SQL analysis pipelines for all projects
