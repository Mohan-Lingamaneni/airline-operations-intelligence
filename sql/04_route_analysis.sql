-- Business question: which routes are the busiest and which routes have the highest delay risk?

-- Minimum route sample size: 5,000 flights
SELECT
    ROUTE,
    COUNT(*) AS flight_count,
    SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct,
    ROUND(AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END), 2) AS avg_arrival_delay,
    ROUND(AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END), 2) AS median_arrival_delay
FROM flights_operations
GROUP BY ROUTE
HAVING COUNT(*) >= 5000
ORDER BY flight_count DESC;

-- Highest-volume routes
SELECT ROUTE, COUNT(*) AS flight_count
FROM flights_operations
GROUP BY ROUTE
HAVING COUNT(*) >= 5000
ORDER BY flight_count DESC;

-- Highest-delay-risk routes
SELECT
    ROUTE,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct
FROM flights_operations
GROUP BY ROUTE
HAVING COUNT(*) >= 5000
ORDER BY late_arrival_rate_pct DESC;

-- Most reliable routes
SELECT
    ROUTE,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct
FROM flights_operations
GROUP BY ROUTE
HAVING COUNT(*) >= 5000
ORDER BY late_arrival_rate_pct ASC;
