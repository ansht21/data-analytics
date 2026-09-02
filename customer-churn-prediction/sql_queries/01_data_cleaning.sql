-- ============================================================
-- 01_data_cleaning.sql - Load & clean Telco churn data (MySQL)
-- Source: data/Telco_Customer_Churn.csv (7,043 rows)
-- ============================================================

-- 1. Create table with explicit types (dates/types fixed at load)
CREATE TABLE IF NOT EXISTS telco_churn (
    customerID       VARCHAR(20) PRIMARY KEY,
    gender           VARCHAR(10),
    SeniorCitizen    TINYINT,
    Partner          VARCHAR(5),
    Dependents       VARCHAR(5),
    tenure           INT,
    PhoneService     VARCHAR(5),
    MultipleLines    VARCHAR(20),
    InternetService  VARCHAR(20),
    OnlineSecurity   VARCHAR(20),
    OnlineBackup     VARCHAR(20),
    DeviceProtection VARCHAR(20),
    TechSupport      VARCHAR(20),
    StreamingTV      VARCHAR(20),
    StreamingMovies  VARCHAR(20),
    Contract         VARCHAR(30),
    PaperlessBilling VARCHAR(5),
    PaymentMethod    VARCHAR(30),
    MonthlyCharges   DECIMAL(10,2),
    TotalCharges     DECIMAL(12,2),
    Churn            VARCHAR(5)
);

-- 2. Import (MySQL Workbench: Table Data Import Wizard -> this CSV)
--    or: LOAD DATA INFILE 'Telco_Customer_Churn.csv' INTO TABLE telco_churn
--        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
--        LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- 3. Data-quality audit (mirrors the notebook's checks)
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT customerID) AS unique_ids FROM telco_churn;
-- Duplicate check: the two counts must be equal

SELECT COUNT(*) AS blank_total_charges FROM telco_churn WHERE TotalCharges IS NULL OR TotalCharges = '';
-- 11 rows: brand-new customers (tenure = 0). Kept in analysis, TotalCharges treated as 0.

-- 4. Flag cleaning: normalise target
SELECT Churn, COUNT(*) FROM telco_churn GROUP BY Churn;   -- expect Yes/No only

-- 5. Churn flag column for analysis
ALTER TABLE telco_churn ADD COLUMN churn_flag TINYINT;
UPDATE telco_churn SET churn_flag = CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END;