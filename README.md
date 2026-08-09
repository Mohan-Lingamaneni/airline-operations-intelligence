# Airline Operations Intelligence

End-to-end airline operations analytics project using U.S. Bureau of Transportation Statistics flight data.

## Project flow

1. Inspect the raw flight data and document structure.
2. Audit data quality and operational risk signals.
3. Create reproducible processed datasets.
4. Run exploratory data analysis and statistical summaries.
5. Build local SQL analytics on SQLite for interview-friendly analysis.

## Data files

- Raw source: data/raw/On_Time_Reporting_Carrier_(2025_01).csv
- Processed operations dataset: data/processed/flights_operations_2025_01.csv
- Processed delay-analysis dataset: data/processed/flights_delay_analysis_2025_01.csv
- SQLite database: data/airline_operations.db
- SQL outputs: data/processed/sql_results/

## SQL analytics

The SQL workflow uses a local SQLite database and query files in the sql folder.

- Build the database: python src/build_database.py
- Run the SQL analytics: python src/run_sql_analytics.py

The SQL scripts cover:
- Overall KPIs
- Airline performance
- Airport performance
- Route analysis
- Time-pattern analysis
- Delay-cause analysis
- Advanced analysis
