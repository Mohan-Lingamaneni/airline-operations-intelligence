-- Business question: when are delays concentrated across the day and week?

-- Hourly arrival delay rate by departure hour
SELECT
    CRS_DEP_TIME_HOUR AS departure_hour,
    COUNT(*) AS flight_count,
    SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct,
    ROUND(AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END), 2) AS avg_arrival_delay
FROM flights_operations
GROUP BY CRS_DEP_TIME_HOUR
ORDER BY departure_hour;

-- Day-of-week pattern
SELECT
    DAY_OF_WEEK,
    COUNT(*) AS flight_count,
    SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct,
    ROUND(AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END), 2) AS avg_arrival_delay
FROM flights_operations
GROUP BY DAY_OF_WEEK
ORDER BY DAY_OF_WEEK;

-- Month-day pattern (calendar day for January)
SELECT
    DAY_OF_MONTH,
    COUNT(*) AS flight_count,
    SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct
FROM flights_operations
GROUP BY DAY_OF_MONTH
ORDER BY DAY_OF_MONTH;
