-- =========================================================================
-- Project: Ride Demand Forecasting & Revenue Analytics
-- Script:  02_Revenue_Analysis.sql
-- Description: Core business intelligence queries covering trip volume,
--              revenue breakdowns, peak demand windows, vehicle performance,
--              airport trip share, pickup hotspots, and weekend behavior.
--
-- Each section states the BUSINESS QUESTION it answers, the metric used, and
-- the answer obtained from the 35,000-trip dataset. Findings are cross-
-- referenced to the Q-numbers in this project's README.
-- =========================================================================

USE UberTripDB;

-- -------------------------------------------------------------------------
-- 1. BUSINESS QUESTION: What is the overall health of the ride business?
-- Metric: trip count, total/average fare, average distance, duration, rating
-- Answer: 35,000 trips | Rs 1,35,44,703 revenue | Rs 387 avg fare
--         | 17.45 km avg distance | 45.5 min avg duration | 4.32 avg rating
-- -------------------------------------------------------------------------
SELECT
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_inr,
    ROUND(AVG(Trip_Distance_km), 2)         AS avg_distance_km,
    ROUND(AVG(Trip_Duration_min), 2)        AS avg_duration_min,
    ROUND(AVG(Rating), 2)                   AS avg_driver_rating
FROM uber_trips_final;


-- -------------------------------------------------------------------------
-- 2. BUSINESS QUESTION: Which hours should we surge-price and add drivers to?
-- Metric: trips + revenue by hour of day, ranked by volume
-- Answer: 6-7 PM is the single peak hour (4,053 trips, Rs 17.8L). The 5-7 PM
--         window carries 10,931 trips = 31.2% of all demand in 3 of 24 hours.
--         A second, smaller peak sits at 8-9 AM (4,721 trips).
-- Action: Concentrate driver incentives on 5-7 PM; surge here first. (README Q1)
-- -------------------------------------------------------------------------
SELECT
    Hour,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_inr,
    RANK() OVER (ORDER BY COUNT(Trip_ID) DESC) AS demand_rank
FROM uber_trips_final
GROUP BY Hour
ORDER BY total_trips DESC;


-- -------------------------------------------------------------------------
-- 3. BUSINESS QUESTION: Which vehicle category earns most per kilometre driven,
--    so we know which fleet to expand?
-- Metric: revenue, avg fare, and revenue-per-km by vehicle type
-- Answer: Uber Black earns Rs 40.06/km -- 2.8x Uber Pool's Rs 14.08/km -- on
--         only 3,566 trips (10% of volume) but Rs 24.9L revenue (18%).
--         UberX is the volume backbone: 13,818 trips, Rs 49.1L.
-- Action: Grow Black supply in high-fare zones; Pool earns least per km. (Q3)
-- -------------------------------------------------------------------------
SELECT
    Vehicle_Type,
    COUNT(Trip_ID)                                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)                              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)                              AS avg_fare_inr,
    ROUND(AVG(Trip_Distance_km), 2)                         AS avg_distance_km,
    ROUND(SUM(Fare_Amount) / SUM(Trip_Distance_km), 2)      AS revenue_per_km
FROM uber_trips_final
GROUP BY Vehicle_Type
ORDER BY total_revenue_inr DESC;


-- -------------------------------------------------------------------------
-- 4. BUSINESS QUESTION: How much of our revenue depends on airport trips?
-- Metric: trip count, revenue, and avg fare split by airport flag
-- Answer: Airport trips are 39.6% of volume but 54.8% of revenue (Rs 74.3L of
--         Rs 135.4L). Avg airport fare Rs 535.77 vs Rs 289.40 non-airport = 1.85x.
-- Action: Airport is the highest-value corridor -- protect supply there. (Q2)
-- -------------------------------------------------------------------------
SELECT
    Is_Airport_Trip,
    COUNT(Trip_ID)                                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)                              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)                              AS avg_fare_inr,
    ROUND(COUNT(Trip_ID) * 100.0 / SUM(COUNT(Trip_ID)) OVER (), 2) AS trip_share_percentage
FROM uber_trips_final
GROUP BY Is_Airport_Trip;


-- -------------------------------------------------------------------------
-- 5. BUSINESS QUESTION: Which pickup zones generate the most revenue?
-- Metric: trips, revenue, avg fare by pickup location
-- Answer: Airport leads with Rs 37.4L (27.6% of revenue) despite having fewer
--         trips than Downtown -- it wins on fare value, not volume.
-- Action: Position premium vehicles at the Airport zone. (Q5)
-- -------------------------------------------------------------------------
SELECT
    Pickup_Location,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_inr
FROM uber_trips_final
GROUP BY Pickup_Location
ORDER BY total_revenue_inr DESC
LIMIT 10;


-- -------------------------------------------------------------------------
-- 6. BUSINESS QUESTION: Should weekend pricing differ from weekday pricing?
-- Metric: volume, revenue, avg fare and distance by weekend flag
-- Answer: No. Avg fare is Rs 389.34 weekend vs Rs 386.05 weekday -- a 0.9%
--         difference, and avg distance is effectively identical (17.51 vs 17.43 km).
-- Action: A weekend-specific pricing tier is NOT justified by this data. A
--         negative finding, reported because it prevents wasted effort. (Q6)
-- -------------------------------------------------------------------------
SELECT
    Is_Weekend,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_inr,
    ROUND(AVG(Trip_Distance_km), 2)         AS avg_distance_km
FROM uber_trips_final
GROUP BY Is_Weekend;


-- -------------------------------------------------------------------------
-- 7. BUSINESS QUESTION: Which part of the day contributes most revenue?
-- Metric: trips, revenue, avg fare by time-of-day bucket
-- Answer: Afternoon (12-18) leads at Rs 52.2L from 13,257 trips. Night (0-6) is
--         the weakest at Rs 9.2L and also the lowest avg fare (Rs 336.77).
-- Action: Minimum-guarantee incentives are needed to keep night supply. (Q7)
-- -------------------------------------------------------------------------
SELECT
    Time_Period,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_inr
FROM uber_trips_final
GROUP BY Time_Period
ORDER BY total_revenue_inr DESC;


-- -------------------------------------------------------------------------
-- 8. BUSINESS QUESTION: Is there visible within-year variation in this dataset?
-- Metric: trips, revenue, avg fare by month
-- Answer: Monthly revenue sits in a narrow Rs 10.7L-11.9L band in this single
--         simulated year. This is descriptive only, not evidence that recurring
--         seasonality is absent.
-- Action: Use time-of-day for current capacity decisions; validate seasonality
--         with multiple years of production data before making annual plans. (Q8)
-- -------------------------------------------------------------------------
SELECT
    Month,
    COUNT(Trip_ID)                          AS total_trips,
    ROUND(SUM(Fare_Amount), 2)              AS total_revenue_inr,
    ROUND(AVG(Fare_Amount), 2)              AS avg_fare_inr
FROM uber_trips_final
GROUP BY Month
ORDER BY Month ASC;


-- =========================================================================
-- ADVANCED ANALYSIS
-- Sections 9-11 go beyond single-table aggregation, using CTEs and window
-- functions (LAG, running SUM OVER) to answer questions that a plain
-- GROUP BY cannot.
-- =========================================================================


-- -------------------------------------------------------------------------
-- 9. BUSINESS QUESTION: Which hour has the sharpest jump in demand -- i.e.
--    where does the evening rush actually START, so incentives go live in time?
-- Metric: hour-over-hour % change in trip volume, plus revenue for context, via LAG()
-- Technique: LAG() window function to compare each hour to the previous one
-- Answer: The result reports the largest hour-over-hour change in trip volume.
--         Read the output values after loading the dataset; revenue is retained
--         as context but does not determine the demand-surge signal.
-- Action: Push driver incentives live by 4:30 PM, an hour before the peak.
--         Peak volume and peak GROWTH are different hours; only LAG shows this.
-- -------------------------------------------------------------------------
WITH hourly_demand AS (
    SELECT
        Hour,
        COUNT(Trip_ID)             AS total_trips,
        ROUND(SUM(Fare_Amount), 2) AS revenue_inr
    FROM uber_trips_final
    GROUP BY Hour
)
SELECT
    Hour,
    total_trips,
    revenue_inr,
    LAG(total_trips) OVER (ORDER BY Hour) AS prev_hour_trips,
    ROUND(
        (total_trips - LAG(total_trips) OVER (ORDER BY Hour))
        / LAG(total_trips) OVER (ORDER BY Hour) * 100
    , 2) AS trip_pct_change_vs_prev_hour,
    CASE
        WHEN total_trips > LAG(total_trips) OVER (ORDER BY Hour) * 1.5 THEN 'DEMAND SURGE'
        WHEN total_trips < LAG(total_trips) OVER (ORDER BY Hour) * 0.7 THEN 'SHARP DROP'
        ELSE 'STABLE'
    END AS demand_signal
FROM hourly_demand
ORDER BY Hour;


-- -------------------------------------------------------------------------
-- 10. BUSINESS QUESTION: How concentrated is revenue by pickup zone -- can we
--     cover most of the business by focusing on just a few zones?
-- Metric: cumulative running share of revenue by zone (Pareto / 80-20 test)
-- Technique: running SUM() OVER (ORDER BY ...) against a window total
-- Answer: NO -- revenue is remarkably evenly spread. It takes 4 of 5 zones to
--         reach 80% of revenue. Airport is the only standout at 27.6%; the
--         other four each contribute 17-19%.
-- Action: A "focus on the top zones" strategy will NOT work here -- coverage
--         must stay city-wide. Only Airport justifies special treatment.
--         Reported as a negative result: the 80/20 assumption fails this data.
-- -------------------------------------------------------------------------
WITH zone_revenue AS (
    SELECT
        Pickup_Location,
        COUNT(Trip_ID)             AS total_trips,
        ROUND(SUM(Fare_Amount), 2) AS revenue_inr
    FROM uber_trips_final
    GROUP BY Pickup_Location
)
SELECT
    Pickup_Location,
    total_trips,
    revenue_inr,
    ROUND(revenue_inr * 100.0 / SUM(revenue_inr) OVER (), 2) AS pct_of_total_revenue,
    ROUND(
        SUM(revenue_inr) OVER (ORDER BY revenue_inr DESC
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        * 100.0 / SUM(revenue_inr) OVER ()
    , 2) AS cumulative_pct_of_revenue,
    ROW_NUMBER() OVER (ORDER BY revenue_inr DESC) AS revenue_rank
FROM zone_revenue
ORDER BY revenue_inr DESC;


-- -------------------------------------------------------------------------
-- 11. BUSINESS QUESTION: Do higher-rated drivers earn more per trip? Should
--     we route premium demand to our best-rated drivers?
-- Metric: avg fare, distance, and fare-per-km by driver-rating band
-- Technique: CASE WHEN bucketing + window share of total
-- Answer: Counter-intuitively, NO -- the LOWEST-rated band (<4.0) has the
--         HIGHEST avg fare (Rs 419.18) and the top band (4.8-5.0) the lowest
--         (Rs 364.24). But the cause is trip length, not driver quality:
--         low-rated drivers average 18.94 km vs 16.25 km for top-rated.
--         Long trips simply cost more AND rate worse.
-- Action: Do NOT read this as "bad drivers earn more". Fare-per-km is the fair
--         comparison, and it is nearly flat across bands. The real insight is
--         that long trips depress ratings -- investigate rider experience on
--         trips over ~18 km rather than penalising the drivers. (README Q4)
-- -------------------------------------------------------------------------
SELECT
    CASE
        WHEN Rating >= 4.8 THEN 'A: 4.8 - 5.0 (Excellent)'
        WHEN Rating >= 4.5 THEN 'B: 4.5 - 4.79 (Good)'
        WHEN Rating >= 4.0 THEN 'C: 4.0 - 4.49 (Average)'
        ELSE                     'D: Below 4.0 (Needs Review)'
    END AS rating_band,
    COUNT(Trip_ID)                                     AS total_trips,
    ROUND(SUM(Fare_Amount), 2)                         AS revenue_inr,
    ROUND(AVG(Fare_Amount), 2)                         AS avg_fare_inr,
    ROUND(AVG(Trip_Distance_km), 2)                    AS avg_distance_km,
    -- the fair like-for-like comparison, controlling for trip length
    ROUND(SUM(Fare_Amount) / SUM(Trip_Distance_km), 2) AS fare_per_km,
    ROUND(COUNT(Trip_ID) * 100.0 / SUM(COUNT(Trip_ID)) OVER (), 2) AS pct_of_trips
FROM uber_trips_final
GROUP BY rating_band
ORDER BY rating_band;
