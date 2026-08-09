-- Business question: what is the overall operational reliability profile of January 2025 flights?

-- Total scheduled flights
SELECT COUNT(*) AS total_scheduled_flights FROM flights_operations;

-- Operated flights (excluding cancellations)
SELECT SUM(CASE WHEN CANCELLED = 0 THEN 1 ELSE 0 END) AS operated_flights
FROM flights_operations;

-- Cancelled flights
SELECT SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) AS cancelled_flights
FROM flights_operations;

-- Cancellation rate
SELECT ROUND(100.0 * SUM(CASE WHEN CANCELLED = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancellation_rate_pct
FROM flights_operations;

-- Diverted flights
SELECT SUM(CASE WHEN DIVERTED = 1 THEN 1 ELSE 0 END) AS diverted_flights
FROM flights_operations;

-- Diversion rate
SELECT ROUND(100.0 * SUM(CASE WHEN DIVERTED = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS diversion_rate_pct
FROM flights_operations;

-- Flights arriving 15+ minutes late in the delay-analysis dataset
SELECT SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) AS late_arrival_flights,
       ROUND(100.0 * SUM(CASE WHEN ARR_DEL15 = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_arrival_rate_pct
FROM flights_delay_analysis;

-- Flights departing 15+ minutes late in the operated dataset
SELECT SUM(CASE WHEN DEP_DEL15 = 1 THEN 1 ELSE 0 END) AS late_departure_flights,
       ROUND(100.0 * SUM(CASE WHEN DEP_DEL15 = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_departure_rate_pct
FROM flights_operations
WHERE CANCELLED = 0;

-- Average arrival delay for operated flights only
SELECT ROUND(AVG(ARR_DELAY), 2) AS avg_arrival_delay
FROM flights_operations
WHERE CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL;

-- Median arrival delay (SQLite-compatible approximation using window functions)
SELECT ROUND(AVG(ARR_DELAY), 2) AS median_arrival_delay
FROM (
    SELECT ARR_DELAY,
           ROW_NUMBER() OVER (ORDER BY ARR_DELAY) AS rn,
           COUNT(*) OVER () AS total_count
    FROM flights_operations
    WHERE CANCELLED = 0 AND DIVERTED = 0 AND ARR_DELAY IS NOT NULL
) t
WHERE rn IN ((total_count + 1) / 2, (total_count + 2) / 2);

-- Average departure delay for operated flights only
SELECT ROUND(AVG(DEP_DELAY), 2) AS avg_departure_delay
FROM flights_operations
WHERE CANCELLED = 0 AND DIVERTED = 0 AND DEP_DELAY IS NOT NULL;
