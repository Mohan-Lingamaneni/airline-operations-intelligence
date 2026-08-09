-- Business question: which airlines have the highest volume and which have the strongest delay performance?

-- Minimum volume threshold for ranking: 10,000 scheduled flights
WITH carrier_base AS (
    SELECT
        OP_UNIQUE_CARRIER AS carrier,
        COUNT(*) AS scheduled_flights,
        SUM(CASE WHEN CANCELLED = 0 THEN 1 ELSE 0 END) AS operated_flights,
        SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
        AVG(CASE WHEN ARR_DEL15 IS NOT NULL THEN ARR_DEL15 ELSE NULL END) AS late_arrival_rate,
        AVG(CASE WHEN CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL THEN ARR_DELAY ELSE NULL END) AS avg_arrival_delay,
        SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) AS cancelled_flights,
        SUM(CASE WHEN DIVERTED = 1 THEN 1 ELSE 0 END) AS diverted_flights
    FROM flights_operations
    GROUP BY OP_UNIQUE_CARRIER
)
SELECT
    carrier,
    scheduled_flights,
    operated_flights,
    late_arrival_flights,
    ROUND(100.0 * late_arrival_flights / NULLIF(operated_flights, 0), 2) AS late_arrival_rate_pct,
    ROUND(avg_arrival_delay, 2) AS avg_arrival_delay,
    cancelled_flights,
    ROUND(100.0 * cancelled_flights / NULLIF(scheduled_flights, 0), 2) AS cancellation_rate_pct,
    diverted_flights,
    ROUND(100.0 * diverted_flights / NULLIF(scheduled_flights, 0), 2) AS diversion_rate_pct
FROM carrier_base
WHERE scheduled_flights >= 10000
ORDER BY scheduled_flights DESC;

-- Highest volume carriers
SELECT carrier, scheduled_flights
FROM (
    SELECT
        OP_UNIQUE_CARRIER AS carrier,
        COUNT(*) AS scheduled_flights
    FROM flights_operations
    GROUP BY OP_UNIQUE_CARRIER
) t
WHERE scheduled_flights >= 10000
ORDER BY scheduled_flights DESC;

-- Lowest late-arrival rate among major carriers
SELECT carrier, ROUND(100.0 * late_arrival_flights / NULLIF(operated_flights, 0), 2) AS late_arrival_rate_pct
FROM (
    SELECT
        OP_UNIQUE_CARRIER AS carrier,
        SUM(CASE WHEN CANCELLED = 0 THEN 1 ELSE 0 END) AS operated_flights,
        SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights
    FROM flights_operations
    GROUP BY OP_UNIQUE_CARRIER
) t
WHERE operated_flights >= 10000
ORDER BY late_arrival_rate_pct ASC;

-- Highest late-arrival rate among major carriers
SELECT carrier, ROUND(100.0 * late_arrival_flights / NULLIF(operated_flights, 0), 2) AS late_arrival_rate_pct
FROM (
    SELECT
        OP_UNIQUE_CARRIER AS carrier,
        SUM(CASE WHEN CANCELLED = 0 THEN 1 ELSE 0 END) AS operated_flights,
        SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights
    FROM flights_operations
    GROUP BY OP_UNIQUE_CARRIER
) t
WHERE operated_flights >= 10000
ORDER BY late_arrival_rate_pct DESC;

-- Lowest cancellation rate among major carriers
SELECT carrier, ROUND(100.0 * cancelled_flights / NULLIF(scheduled_flights, 0), 2) AS cancellation_rate_pct
FROM (
    SELECT
        OP_UNIQUE_CARRIER AS carrier,
        COUNT(*) AS scheduled_flights,
        SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) AS cancelled_flights
    FROM flights_operations
    GROUP BY OP_UNIQUE_CARRIER
) t
WHERE scheduled_flights >= 10000
ORDER BY cancellation_rate_pct ASC;
