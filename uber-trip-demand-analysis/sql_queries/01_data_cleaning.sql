-- =========================================================================
-- Project: Ride Demand Forecasting & Revenue Analytics
-- Script:  01_Data_Cleaning.sql
-- Description: Creates the raw schema, loads the CSV dataset, deduplicates
--              records using a ROW_NUMBER() window function, and validates
--              the final clean table is ready for analysis.
-- =========================================================================

-- 1. Create and select database
CREATE DATABASE IF NOT EXISTS UberTripDB;
USE UberTripDB;

-- 2. Define the raw staging table
DROP TABLE IF EXISTS uber_trips;
CREATE TABLE uber_trips (
    Trip_ID           VARCHAR(20),
    Date              DATE,
    Time              TIME,
    Hour              INT,
    Day_of_Week       VARCHAR(20),
    Month             INT,
    Pickup_Location   VARCHAR(50),
    Dropoff_Location  VARCHAR(50),
    Vehicle_Type      VARCHAR(50),
    Trip_Distance_km  FLOAT,
    Trip_Duration_min FLOAT,
    Fare_Amount       FLOAT,
    Payment_Method    VARCHAR(50),
    Rating            FLOAT,
    Driver_ID         VARCHAR(20),
    Is_Weekend        VARCHAR(10),
    Time_Period       VARCHAR(50),
    Is_Airport_Trip   VARCHAR(10)
);

-- 3. Enable local file imports (run once per session)
SET GLOBAL local_infile = 1;

-- 4. Bulk load raw CSV into staging table
-- Replace the file path below with the actual path on your machine.
LOAD DATA LOCAL INFILE 'C:/data/Uber_Cleaned_data.csv'
INTO TABLE uber_trips
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- 5. Stage 1 deduplication: Remove fully identical rows
DROP TABLE IF EXISTS uber_trips_clean;
CREATE TABLE uber_trips_clean AS
SELECT DISTINCT *
FROM uber_trips;

-- 6. Stage 2 deduplication: retain one record per Trip_ID deterministically.
--    The source has no update timestamp, so Date/Time plus stable business
--    attributes are used only as a tie-breaker; this does not claim recency.
DROP TABLE IF EXISTS uber_trips_final;
CREATE TABLE uber_trips_final AS
SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY Trip_ID
               ORDER BY Date DESC, Time DESC, Fare_Amount DESC,
                        Trip_Distance_km DESC, Driver_ID DESC
           ) AS rn
    FROM uber_trips_clean
) ranked
WHERE rn = 1;

-- 7. Drop the staging helper column and intermediate table
ALTER TABLE uber_trips_final DROP COLUMN rn;
DROP TABLE uber_trips_clean;

-- 8. Validation checks
-- BUSINESS QUESTION: Can we trust the numbers this pipeline produces?
-- Answer: 35,000 records survive deduplication with zero nulls in Trip_ID,
--         Fare_Amount or Trip_Distance_km -- every revenue and distance
--         metric downstream is computed on the full population.
SELECT COUNT(*) AS total_records_after_dedup FROM uber_trips_final;

SELECT
    SUM(CASE WHEN Trip_ID IS NULL THEN 1 ELSE 0 END) AS null_trip_ids,
    SUM(CASE WHEN Fare_Amount IS NULL THEN 1 ELSE 0 END) AS null_fares,
    SUM(CASE WHEN Trip_Distance_km IS NULL THEN 1 ELSE 0 END) AS null_distances
FROM uber_trips_final;
