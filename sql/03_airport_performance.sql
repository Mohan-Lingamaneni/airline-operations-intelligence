-- Business question: which origin and destination airports have the heaviest volumes and highest delay risk?

-- Origin airport performance (minimum volume threshold: 10,000 flights)
SELECT
    ORIGIN AS airport,
    COUNT(*) AS flight_count,
    SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct,
    ROUND(AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END), 2) AS avg_arrival_delay,
    SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) AS cancelled_flights,
    ROUND(100.0 * SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS cancellation_rate_pct
FROM flights_operations
GROUP BY ORIGIN
HAVING COUNT(*) >= 10000
ORDER BY flight_count DESC;

-- Highest-volume origins
SELECT ORIGIN AS airport, COUNT(*) AS flight_count
FROM flights_operations
GROUP BY ORIGIN
HAVING COUNT(*) >= 10000
ORDER BY flight_count DESC;

-- Highest-delay-risk origins (high-volume only)
SELECT
    ORIGIN AS airport,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct
FROM flights_operations
GROUP BY ORIGIN
HAVING COUNT(*) >= 10000
ORDER BY late_arrival_rate_pct DESC;

-- Most reliable origins (high-volume only)
SELECT
    ORIGIN AS airport,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct
FROM flights_operations
GROUP BY ORIGIN
HAVING COUNT(*) >= 10000
ORDER BY late_arrival_rate_pct ASC;

-- Destination airport performance
SELECT
    DEST AS airport,
    COUNT(*) AS flight_count,
    SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct,
    ROUND(AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END), 2) AS avg_arrival_delay,
    SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) AS cancelled_flights,
    ROUND(100.0 * SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS cancellation_rate_pct
FROM flights_operations
GROUP BY DEST
HAVING COUNT(*) >= 10000
ORDER BY flight_count DESC;
