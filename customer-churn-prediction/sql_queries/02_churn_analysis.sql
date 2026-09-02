-- =========================================================================
-- Project: Customer Churn Analysis - Subscription Retention Analytics
-- Script:  02_churn_analysis.sql
-- Description: Core business intelligence queries covering the KPI baseline,
--              contract/tenure/payment segments, the fiber-optic confounder
--              check, and the revenue-at-risk prioritisation.
--
-- Each section states the BUSINESS QUESTION it answers, the metric used, and
-- the answer obtained from the 7,032-customer cleaned dataset. Findings are
-- cross-referenced to the Q-numbers in this project's README.
-- =========================================================================

USE ChurnDB;

-- -------------------------------------------------------------------------
-- 1. BUSINESS QUESTION: What is the overall health of the customer base?
-- Metric: customer count, churn rate, monthly revenue, revenue at risk
-- Answer: 7,032 customers | 1,869 churned | 26.6% churn rate
--         | $455,661 monthly revenue | $139,131 monthly revenue at risk
--         | 32.4 months avg tenure | $64.8 avg monthly charge
-- -------------------------------------------------------------------------
SELECT
    COUNT(*)                                         AS customers,
    SUM(churn_flag)                                  AS churned,
    ROUND(AVG(churn_flag), 4)                        AS churn_rate,
    ROUND(SUM(MonthlyCharges), 0)                    AS monthly_revenue,
    ROUND(SUM(CASE WHEN churn_flag = 1 THEN MonthlyCharges END), 0) AS monthly_revenue_at_risk,
    ROUND(AVG(tenure), 1)                            AS avg_tenure_months,
    ROUND(AVG(MonthlyCharges), 2)                    AS avg_monthly_charge
FROM telco_churn;

-- -------------------------------------------------------------------------
-- 2. BUSINESS QUESTION: Which contract type churns most? (README Q1)
-- Metric: churn rate + revenue at risk by contract
-- Answer: Month-to-month churn rate 42.7% (of 3,875 customers, $120,847
--         monthly revenue at risk) vs One year 11.3% and Two year 2.8%.
-- Action: Push annual conversion early in the customer lifecycle.
-- -------------------------------------------------------------------------
SELECT Contract,
       COUNT(*)                  AS customers,
       ROUND(AVG(churn_flag), 3) AS churn_rate,
       ROUND(SUM(CASE WHEN churn_flag = 1 THEN MonthlyCharges END), 2) AS monthly_rev_at_risk
FROM telco_churn
GROUP BY Contract
ORDER BY churn_rate DESC;

-- -------------------------------------------------------------------------
-- 3. BUSINESS QUESTION: When do customers leave? (README Q2)
-- Metric: churn rate by tenure band, with LAG() to show the drop between bands
-- Answer: Churn falls steadily with tenure - the first 12 months are the
--         danger window; 4-year-plus customers rarely leave.
-- Action: Onboarding and early check-ins for new customers.
-- -------------------------------------------------------------------------
SELECT
    CASE WHEN tenure <= 6  THEN '0-6m'
         WHEN tenure <= 12 THEN '7-12m'
         WHEN tenure <= 24 THEN '13-24m'
         WHEN tenure <= 48 THEN '25-48m'
         ELSE '49-72m' END                                AS tenure_band,
    COUNT(*)                                              AS customers,
    ROUND(AVG(churn_flag), 3)                             AS churn_rate,
    LAG(ROUND(AVG(churn_flag), 3)) OVER (ORDER BY MIN(tenure)) AS prev_band_rate
FROM telco_churn
GROUP BY tenure_band, MIN(tenure)
ORDER BY MIN(tenure);

-- -------------------------------------------------------------------------
-- 4. BUSINESS QUESTION: Which services and payment methods churn hardest?
--    (README Q3)
-- Metric: churn rate by internet service and by payment method
-- Answer: Fiber optic 41.9% vs DSL 19.0% vs no internet 7.4%.
--         Electronic check 45.3% vs automatic payments 15-17%.
-- Action: Service-quality outreach for fiber customers; auto-pay incentives.
-- -------------------------------------------------------------------------
SELECT InternetService, ROUND(AVG(churn_flag), 3) AS churn_rate
FROM telco_churn GROUP BY InternetService ORDER BY churn_rate DESC;

SELECT PaymentMethod, ROUND(AVG(churn_flag), 3) AS churn_rate
FROM telco_churn GROUP BY PaymentMethod ORDER BY churn_rate DESC;

-- -------------------------------------------------------------------------
-- 5. BUSINESS QUESTION: Is fiber-optic churn the service itself, or the
--    contract mix that buys it? (README Q4 - confounder check)
-- Metric: churn rate by internet service WITHIN each contract type
-- Answer: Within every contract type fiber churns more than DSL, but the
--         gap narrows sharply on long contracts - both the service and the
--         month-to-month mix contribute.
-- Action: Target the right lever per segment, not a single blanket fix.
-- -------------------------------------------------------------------------
SELECT InternetService, Contract,
       COUNT(*)                  AS customers,
       ROUND(AVG(churn_flag), 3) AS churn_rate
FROM telco_churn
WHERE InternetService IN ('Fiber optic', 'DSL')
GROUP BY InternetService, Contract
ORDER BY InternetService, Contract;

-- -------------------------------------------------------------------------
-- 6. BUSINESS QUESTION: Where is revenue at risk concentrated? (README Q5)
-- Metric: contract x service segments ranked by monthly revenue at risk
-- Answer: Month-to-month + fiber optic is the top segment by far - 2,128
--         customers, 54.6% churn rate, $100,482 monthly revenue at risk
--         (72% of the total). RANK() makes the prioritisation explicit.
-- Action: Point retention spend at the top-ranked segments first.
-- -------------------------------------------------------------------------
SELECT Contract, InternetService,
       COUNT(*)                                                      AS customers,
       ROUND(AVG(churn_flag), 3)                                     AS churn_rate,
       ROUND(SUM(CASE WHEN churn_flag = 1 THEN MonthlyCharges END), 2) AS monthly_rev_at_risk,
       RANK() OVER (ORDER BY SUM(CASE WHEN churn_flag = 1 THEN MonthlyCharges END) DESC) AS priority_rank
FROM telco_churn
GROUP BY Contract, InternetService
ORDER BY monthly_rev_at_risk DESC;

-- -------------------------------------------------------------------------
-- 7. BUSINESS QUESTION: Do churned customers pay differently?
-- Metric: monthly-charge distribution by churn status (spread check)
-- Answer: Churned customers average a higher monthly bill than retained
--         ones - price sensitivity is part of the churn story.
-- Action: Watch price increases for at-risk cohorts.
-- -------------------------------------------------------------------------
SELECT Churn,
       ROUND(AVG(MonthlyCharges), 2)           AS avg_monthly,
       ROUND(STDDEV_SAMP(MonthlyCharges), 2)   AS std_monthly,
       ROUND(MIN(MonthlyCharges), 2)           AS min_monthly,
       ROUND(MAX(MonthlyCharges), 2)           AS max_monthly
FROM telco_churn
GROUP BY Churn;