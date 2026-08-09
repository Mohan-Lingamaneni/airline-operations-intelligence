-- Business question: which carriers and airports are most associated with high-delay corridors?

-- Carriers with the highest share of late arrivals at high-volume airports
SELECT
    OP_UNIQUE_CARRIER AS carrier,
    ORIGIN AS origin_airport,
    DEST AS destination_airport,
    COUNT(*) AS flight_count,
    SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct
FROM flights_operations
WHERE ORIGIN IN (
    SELECT ORIGIN
    FROM flights_operations
    GROUP BY ORIGIN
    HAVING COUNT(*) >= 10000
)
GROUP BY OP_UNIQUE_CARRIER, ORIGIN, DEST
HAVING COUNT(*) >= 5000
ORDER BY late_arrival_rate_pct DESC, flight_count DESC;

-- Correlation-like ranking of routes by volume and lateness
SELECT
    ROUTE,
    COUNT(*) AS flight_count,
    ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS late_arrival_rate_pct,
    ROUND(AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END), 2) AS avg_arrival_delay
FROM flights_operations
GROUP BY ROUTE
HAVING COUNT(*) >= 10000
ORDER BY late_arrival_rate_pct DESC, flight_count DESC;
