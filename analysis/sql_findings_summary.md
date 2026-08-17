# SQL Analysis Findings

This analysis uses the processed January 2025 airline operations dataset and the SQLite database created for the project.

## Overall Performance

- Total scheduled flights: 539,747
- Cancellation rate: approximately 3.02%
- Diversion rate: approximately 0.22%
- Arrival delay rate of 15 minutes or more: approximately 18.79%
- Departure delay rate of 15 minutes or more: approximately 18.2%

The median arrival delay was negative while the mean arrival delay was positive, showing that most flights arrived near or ahead of schedule while a smaller number of severe delays pulled the average upward.

## Airline Performance

SQL queries were used to compare carriers by:

- Flight volume
- Arrival delay rate
- Cancellation rate
- Average arrival delay

The analysis showed noticeable differences in operational performance across airlines, although performance should be interpreted alongside flight volume and route mix.

## Airport and Route Analysis

Airport-level queries were used to compare origin and destination activity and delay performance.

DFW, DEN, ATL, ORD, and CLT were among the highest-volume airports in the January dataset.

Route analysis was also performed using minimum flight-volume thresholds to avoid drawing conclusions from routes with very small sample sizes.

## Time-Based Patterns

Delay performance varied throughout the day.

Morning flights generally showed lower late-arrival rates, while afternoon, evening, and late-night periods showed higher delay risk.

This suggests that operational disruptions may accumulate as the day progresses.

## Delay Causes

The dataset includes several reported delay categories:

- Carrier delay
- Late aircraft delay
- NAS delay
- Weather delay
- Security delay

Carrier delay and late-aircraft delay accounted for the largest total delay minutes among the reported categories.

These fields are structurally missing for many flights, so they are treated as descriptive measures rather than complete causal evidence.

## Key Takeaway

The SQL analysis shows how operational performance can be evaluated across airlines, airports, routes, and time periods using reusable queries and KPI-based reporting.

The next phase of the project will focus on turning these analytical outputs into a dashboard for easier exploration and communication.
