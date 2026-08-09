-- Business question: which delay causes are most common in the January 2025 operations data?

SELECT
    CARRIER_DELAY,
    WEATHER_DELAY,
    NAS_DELAY,
    SECURITY_DELAY,
    LATE_AIRCRAFT_DELAY,
    ARR_DELAY
FROM flights_delay_analysis
LIMIT 20;

-- Count rows with non-null delay cause values
SELECT
    SUM(CASE WHEN CARRIER_DELAY IS NOT NULL AND CARRIER_DELAY > 0 THEN 1 ELSE 0 END) AS carrier_delay_rows,
    SUM(CASE WHEN WEATHER_DELAY IS NOT NULL AND WEATHER_DELAY > 0 THEN 1 ELSE 0 END) AS weather_delay_rows,
    SUM(CASE WHEN NAS_DELAY IS NOT NULL AND NAS_DELAY > 0 THEN 1 ELSE 0 END) AS nas_delay_rows,
    SUM(CASE WHEN SECURITY_DELAY IS NOT NULL AND SECURITY_DELAY > 0 THEN 1 ELSE 0 END) AS security_delay_rows,
    SUM(CASE WHEN LATE_AIRCRAFT_DELAY IS NOT NULL AND LATE_AIRCRAFT_DELAY > 0 THEN 1 ELSE 0 END) AS late_aircraft_delay_rows
FROM flights_delay_analysis;

-- Aggregate total minutes by delay cause
SELECT
    'carrier' AS cause,
    SUM(CARRIER_DELAY) AS total_minutes
FROM flights_delay_analysis
UNION ALL
SELECT
    'weather',
    SUM(WEATHER_DELAY)
FROM flights_delay_analysis
UNION ALL
SELECT
    'nas',
    SUM(NAS_DELAY)
FROM flights_delay_analysis
UNION ALL
SELECT
    'security',
    SUM(SECURITY_DELAY)
FROM flights_delay_analysis
UNION ALL
SELECT
    'late_aircraft',
    SUM(LATE_AIRCRAFT_DELAY)
FROM flights_delay_analysis
ORDER BY total_minutes DESC;
