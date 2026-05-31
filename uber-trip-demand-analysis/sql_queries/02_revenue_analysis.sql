-- =========================================================================
-- Project: Ride Demand Forecasting & Revenue Analytics
-- Script:  02_Revenue_Analysis.sql
-- Description: Core business intelligence queries covering trip volume,
--              revenue breakdowns, peak demand windows, vehicle performance,
--              airport trip share, pickup hotspots, and weekend behavior.
-- =========================================================================

USE UberTripDB;

-- -------------------------------------------------------------------------
-- 1. Portfolio KPI Summary
-- -------------------------------------------------------------------------
SELECT
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_usd,
    ROUND(AVG(Trip_Distance_km), 2)         AS avg_distance_km,
    ROUND(AVG(Trip_Duration_min), 2)        AS avg_duration_min,
    ROUND(AVG(Rating), 2)                   AS avg_driver_rating
FROM uber_trips_final;


-- -------------------------------------------------------------------------
-- 2. Hourly Demand & Revenue Heatmap
-- Description: Identifies which hours generate the highest trip volume
--              and revenue — used for surge pricing and driver allocation.
-- -------------------------------------------------------------------------
SELECT
    Hour,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_usd,
    RANK() OVER (ORDER BY COUNT(Trip_ID) DESC) AS demand_rank
FROM uber_trips_final
GROUP BY Hour
ORDER BY total_trips DESC;


-- -------------------------------------------------------------------------
-- 3. Vehicle Category Financial Performance
-- Description: Compares each vehicle type on revenue, average fare,
--              and revenue-per-km efficiency.
-- -------------------------------------------------------------------------
SELECT
    Vehicle_Type,
    COUNT(Trip_ID)                                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)                              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)                              AS avg_fare_usd,
    ROUND(AVG(Trip_Distance_km), 2)                         AS avg_distance_km,
    ROUND(SUM(Fare_Amount) / SUM(Trip_Distance_km), 2)      AS revenue_per_km
FROM uber_trips_final
GROUP BY Vehicle_Type
ORDER BY total_revenue_usd DESC;


-- -------------------------------------------------------------------------
-- 4. Airport vs. Standard Trip Comparison
-- Description: Quantifies the share of airport-related bookings and their
--              impact on total revenue.
-- -------------------------------------------------------------------------
SELECT
    Is_Airport_Trip,
    COUNT(Trip_ID)                                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)                              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)                              AS avg_fare_usd,
    ROUND(COUNT(Trip_ID) * 100.0 / SUM(COUNT(Trip_ID)) OVER (), 2) AS trip_share_percentage
FROM uber_trips_final
GROUP BY Is_Airport_Trip;


-- -------------------------------------------------------------------------
-- 5. Top 10 Revenue-Generating Pickup Locations
-- Description: Identifies high-demand zones for premium vehicle positioning
--              and surge pricing zone definitions.
-- -------------------------------------------------------------------------
SELECT
    Pickup_Location,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_usd
FROM uber_trips_final
GROUP BY Pickup_Location
ORDER BY total_revenue_usd DESC
LIMIT 10;


-- -------------------------------------------------------------------------
-- 6. Weekend vs. Weekday Behavioral Analysis
-- Description: Compares demand volume and fare patterns across weekdays
--              vs. weekends to guide pricing strategy.
-- -------------------------------------------------------------------------
SELECT
    Is_Weekend,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_usd,
    ROUND(AVG(Trip_Distance_km), 2)         AS avg_distance_km
FROM uber_trips_final
GROUP BY Is_Weekend;


-- -------------------------------------------------------------------------
-- 7. Time-of-Day Period Analysis (Morning / Afternoon / Evening / Night)
-- Description: Aggregates trips by pre-built time period labels to identify
--              macro-level demand trends by part of day.
-- -------------------------------------------------------------------------
SELECT
    Time_Period,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_usd
FROM uber_trips_final
GROUP BY Time_Period
ORDER BY total_revenue_usd DESC;


-- -------------------------------------------------------------------------
-- 8. Monthly Revenue Trend
-- Description: Tracks cumulative monthly revenue to identify seasonal
--              demand cycles and growth trajectories.
-- -------------------------------------------------------------------------
SELECT
    Month,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_usd,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_usd
FROM uber_trips_final
GROUP BY Month
ORDER BY Month ASC;
