"""Exploratory data analysis and statistical analysis for the BTS flight datasets.

This script creates analytical summary tables, runs basic statistical tests,
and saves a small set of professional charts. It does not build models or
modify the processed datasets.
"""

from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPERATIONS_PATH = PROJECT_ROOT / "data" / "processed" / "flights_operations_2025_01.csv"
DELAY_PATH = PROJECT_ROOT / "data" / "processed" / "flights_delay_analysis_2025_01.csv"
ANALYSIS_DIR = PROJECT_ROOT / "data" / "processed" / "analysis"
IMAGES_DIR = PROJECT_ROOT / "images" / "eda"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    operations = pd.read_csv(OPERATIONS_PATH)
    delay = pd.read_csv(DELAY_PATH)
    return operations, delay


def summarize_overall_kpis(operations: pd.DataFrame, delay: pd.DataFrame) -> pd.DataFrame:
    total_scheduled = len(operations)
    operated = int(operations["CANCELLED"].eq(0).sum())
    cancellation_rate = round(operations["CANCELLED"].mean() * 100, 2)
    diversion_rate = round(operations["DIVERTED"].mean() * 100, 2)
    arr_delay_15_rate = round(delay["ARR_DEL15"].mean() * 100, 2) if "ARR_DEL15" in delay.columns else np.nan
    eligible_operated = operations[(operations["CANCELLED"].fillna(0) == 0) & (operations["DIVERTED"].fillna(0) == 0)]
    dep_delay_eligible = eligible_operated[(eligible_operated["DEP_DELAY"].notna()) & (eligible_operated["DEP_DEL15"].notna())]
    arr_delay_eligible = eligible_operated[eligible_operated["ARR_DELAY"].notna()]
    dep_delay_15_rate = round(dep_delay_eligible["DEP_DEL15"].mean() * 100, 2) if not dep_delay_eligible.empty else np.nan
    arr_delay_mean = round(arr_delay_eligible["ARR_DELAY"].mean(), 2) if not arr_delay_eligible.empty else np.nan
    arr_delay_median = round(arr_delay_eligible["ARR_DELAY"].median(), 2) if not arr_delay_eligible.empty else np.nan
    arr_delay_p75 = round(arr_delay_eligible["ARR_DELAY"].quantile(0.75), 2) if not arr_delay_eligible.empty else np.nan
    arr_delay_p90 = round(arr_delay_eligible["ARR_DELAY"].quantile(0.90), 2) if not arr_delay_eligible.empty else np.nan
    arr_delay_p95 = round(arr_delay_eligible["ARR_DELAY"].quantile(0.95), 2) if not arr_delay_eligible.empty else np.nan
    arr_delay_p99 = round(arr_delay_eligible["ARR_DELAY"].quantile(0.99), 2) if not arr_delay_eligible.empty else np.nan
    dep_delay_mean = round(dep_delay_eligible["DEP_DELAY"].mean(), 2) if not dep_delay_eligible.empty else np.nan
    dep_delay_median = round(dep_delay_eligible["DEP_DELAY"].median(), 2) if not dep_delay_eligible.empty else np.nan

    summary = pd.DataFrame(
        {
            "metric": [
                "total_scheduled_flights",
                "operated_flights",
                "cancellation_rate_percent",
                "diversion_rate_percent",
                "arrival_delay_15_rate_percent",
                "departure_delay_15_rate_percent",
                "mean_arrival_delay",
                "median_arrival_delay",
                "p75_arrival_delay",
                "p90_arrival_delay",
                "p95_arrival_delay",
                "p99_arrival_delay",
                "mean_departure_delay",
                "median_departure_delay",
            ],
            "value": [
                total_scheduled,
                operated,
                cancellation_rate,
                diversion_rate,
                arr_delay_15_rate,
                dep_delay_15_rate,
                arr_delay_mean,
                arr_delay_median,
                arr_delay_p75,
                arr_delay_p90,
                arr_delay_p95,
                arr_delay_p99,
                dep_delay_mean,
                dep_delay_median,
            ],
        }
    )
    return summary


def airline_performance(operations: pd.DataFrame, delay: pd.DataFrame) -> pd.DataFrame:
    min_volume = 10000
    eligible_operated = operations[(operations["CANCELLED"].fillna(0) == 0) & (operations["DIVERTED"].fillna(0) == 0)]
    airline_summary = []
    for carrier, group in operations.groupby("OP_UNIQUE_CARRIER"):
        delay_subset = delay[delay["OP_UNIQUE_CARRIER"] == carrier] if carrier in delay["OP_UNIQUE_CARRIER"].values else pd.DataFrame()
        numeric_subset = eligible_operated[eligible_operated["OP_UNIQUE_CARRIER"] == carrier]
        summary = {
            "carrier": carrier,
            "scheduled_flights": int(len(group)),
            "eligible_operated_flights": int(len(delay_subset)),
            "arrival_delay_15_rate": round(delay_subset["ARR_DEL15"].mean() * 100, 2) if not delay_subset.empty else np.nan,
            "average_arrival_delay": round(numeric_subset["ARR_DELAY"].mean(), 2) if not numeric_subset.empty else np.nan,
            "median_arrival_delay": round(numeric_subset["ARR_DELAY"].median(), 2) if not numeric_subset.empty else np.nan,
            "cancellation_rate": round(group["CANCELLED"].mean() * 100, 2),
            "diversion_rate": round(group["DIVERTED"].mean() * 100, 2),
        }
        airline_summary.append(summary)
    airline_df = pd.DataFrame(airline_summary)
    airline_df = airline_df[airline_df["scheduled_flights"] >= min_volume].copy()
    airline_df = airline_df.sort_values("scheduled_flights", ascending=False)
    return airline_df


def airport_performance(operations: pd.DataFrame, delay: pd.DataFrame, column: str) -> pd.DataFrame:
    min_volume = 10000
    eligible_operated = operations[(operations["CANCELLED"].fillna(0) == 0) & (operations["DIVERTED"].fillna(0) == 0)]
    summary = []
    for airport, group in operations.groupby(column):
        delay_subset = delay[delay[column] == airport] if airport in delay[column].values else pd.DataFrame()
        numeric_subset = eligible_operated[eligible_operated[column] == airport]
        summary.append(
            {
                "airport": airport,
                "flight_volume": int(len(group)),
                "arrival_delay_15_rate": round(delay_subset["ARR_DEL15"].mean() * 100, 2) if not delay_subset.empty else np.nan,
                "average_arrival_delay": round(numeric_subset["ARR_DELAY"].mean(), 2) if not numeric_subset.empty else np.nan,
                "cancellation_rate": round(group["CANCELLED"].mean() * 100, 2),
            }
        )
    airport_df = pd.DataFrame(summary)
    airport_df = airport_df[airport_df["flight_volume"] >= min_volume].copy()
    airport_df = airport_df.sort_values("flight_volume", ascending=False)
    return airport_df


def route_performance(operations: pd.DataFrame, delay: pd.DataFrame) -> pd.DataFrame:
    min_volume = 5000
    eligible_operated = operations[(operations["CANCELLED"].fillna(0) == 0) & (operations["DIVERTED"].fillna(0) == 0)]
    route_summary = (
        operations.groupby("ROUTE")
        .agg(
            flight_count=("ROUTE", "size"),
            cancellation_rate=("CANCELLED", "mean"),
            diversion_rate=("DIVERTED", "mean"),
        )
        .reset_index()
    )
    rate_summary = (
        delay.groupby("ROUTE")
        .agg(arrival_delay_15_rate=("ARR_DEL15", "mean"))
        .reset_index()
    )
    numeric_route = (
        eligible_operated.groupby("ROUTE")
        .agg(average_arrival_delay=("ARR_DELAY", "mean"), median_arrival_delay=("ARR_DELAY", "median"))
        .reset_index()
    )
    route_summary = route_summary.merge(rate_summary, on="ROUTE", how="left")
    route_summary = route_summary.merge(numeric_route, on="ROUTE", how="left")
    route_summary["arrival_delay_15_rate"] = round(route_summary["arrival_delay_15_rate"] * 100, 2)
    route_summary["cancellation_rate"] = round(route_summary["cancellation_rate"] * 100, 2)
    route_summary["diversion_rate"] = round(route_summary["diversion_rate"] * 100, 2)
    route_summary["average_arrival_delay"] = round(route_summary["average_arrival_delay"], 2)
    route_summary["median_arrival_delay"] = round(route_summary["median_arrival_delay"], 2)
    route_summary = route_summary[route_summary["flight_count"] >= min_volume].copy()
    route_summary = route_summary.sort_values("flight_count", ascending=False)
    return route_summary


def time_patterns(delay: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    day_summary = (
        delay.groupby("DAY_OF_WEEK")
        .agg(flight_count=("ARR_DEL15", "size"), arrival_delay_15_rate=("ARR_DEL15", "mean"))
        .reset_index()
    )
    day_summary["arrival_delay_15_rate"] = round(day_summary["arrival_delay_15_rate"] * 100, 2)

    hour_summary = (
        delay.groupby("SCHEDULED_DEP_HOUR")
        .agg(flight_count=("ARR_DEL15", "size"), arrival_delay_15_rate=("ARR_DEL15", "mean"))
        .reset_index()
    )
    hour_summary["arrival_delay_15_rate"] = round(hour_summary["arrival_delay_15_rate"] * 100, 2)

    block_summary = (
        delay.groupby("DEP_TIME_BLOCK_CUSTOM")
        .agg(flight_count=("ARR_DEL15", "size"), arrival_delay_15_rate=("ARR_DEL15", "mean"))
        .reset_index()
    )
    block_summary["arrival_delay_15_rate"] = round(block_summary["arrival_delay_15_rate"] * 100, 2)
    return day_summary, hour_summary, block_summary


def distance_analysis(operations: pd.DataFrame, delay: pd.DataFrame) -> pd.DataFrame:
    eligible_operated = operations[(operations["CANCELLED"].fillna(0) == 0) & (operations["DIVERTED"].fillna(0) == 0)]
    rate_summary = (
        delay.groupby("DISTANCE_GROUP")
        .agg(flight_count=("ARR_DEL15", "size"), arrival_delay_15_rate=("ARR_DEL15", "mean"))
        .reset_index()
    )
    numeric_summary = (
        eligible_operated.groupby("DISTANCE_GROUP")
        .agg(average_arrival_delay=("ARR_DELAY", "mean"))
        .reset_index()
    )
    distance_summary = rate_summary.merge(numeric_summary, on="DISTANCE_GROUP", how="left")
    distance_summary["arrival_delay_15_rate"] = round(distance_summary["arrival_delay_15_rate"] * 100, 2)
    distance_summary["average_arrival_delay"] = round(distance_summary["average_arrival_delay"], 2)
    return distance_summary


def delay_cause_summary(operations: pd.DataFrame) -> pd.DataFrame:
    cause_fields = ["CARRIER_DELAY", "WEATHER_DELAY", "NAS_DELAY", "SECURITY_DELAY", "LATE_AIRCRAFT_DELAY"]
    rows = []
    for field in cause_fields:
        numeric = pd.to_numeric(operations[field], errors="coerce")
        present = numeric.dropna()
        rows.append(
            {
                "cause": field,
                "total_minutes": int(present.sum()),
                "percentage_of_attributed_minutes": round(present.sum() / numeric.dropna().sum() * 100, 2) if present.sum() else np.nan,
                "average_minutes_when_present": round(present.mean(), 2) if not present.empty else np.nan,
                "non_missing_count": int(present.count()),
            }
        )
    summary = pd.DataFrame(rows)
    return summary


def save_csv(df: pd.DataFrame, filename: str) -> None:
    df.to_csv(ANALYSIS_DIR / filename, index=False)


def run_statistical_tests(delay: pd.DataFrame) -> str:
    result_lines = []
    if {"OP_UNIQUE_CARRIER", "ARR_DEL15"}.issubset(delay.columns):
        contingency = pd.crosstab(delay["OP_UNIQUE_CARRIER"], delay["ARR_DEL15"])
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
        cramers_v = np.sqrt(chi2 / (len(delay) * min(contingency.shape[0] - 1, contingency.shape[1] - 1)))
        result_lines.append("Airline vs late arrival")
        result_lines.append(f"- Chi-square statistic: {chi2:.4f}")
        result_lines.append(f"- p-value: {p_value:.6e}")
        result_lines.append(f"- Cramer's V: {cramers_v:.4f}")
        result_lines.append("- Interpretation: p-value is tiny because the sample is large; practical importance should be judged by effect size and business relevance.")

    if {"DEP_TIME_BLOCK_CUSTOM", "ARR_DEL15"}.issubset(delay.columns):
        contingency2 = pd.crosstab(delay["DEP_TIME_BLOCK_CUSTOM"], delay["ARR_DEL15"])
        chi2b, p_value_b, dof_b, expected_b = stats.chi2_contingency(contingency2)
        cramers_v_b = np.sqrt(chi2b / (len(delay) * min(contingency2.shape[0] - 1, contingency2.shape[1] - 1)))
        result_lines.append("\nTime block vs late arrival")
        result_lines.append(f"- Chi-square statistic: {chi2b:.4f}")
        result_lines.append(f"- p-value: {p_value_b:.6e}")
        result_lines.append(f"- Cramer's V: {cramers_v_b:.4f}")

    if {"DISTANCE", "ARR_DELAY"}.issubset(delay.columns):
        pearson = delay[["DISTANCE", "ARR_DELAY"]].corr(method="pearson").iloc[0, 1]
        spearman = delay[["DISTANCE", "ARR_DELAY"]].corr(method="spearman").iloc[0, 1]
        result_lines.append("\nDistance vs arrival delay")
        result_lines.append(f"- Pearson correlation: {pearson:.4f}")
        result_lines.append(f"- Spearman correlation: {spearman:.4f}")
        result_lines.append("- Interpretation: Pearson measures linear association; Spearman measures monotonic rank association.")

    if {"OP_UNIQUE_CARRIER", "ARR_DEL15"}.issubset(delay.columns):
        major_airlines = delay.groupby("OP_UNIQUE_CARRIER").size()
        major_airlines = major_airlines[major_airlines >= 10000].index
        result_lines.append("\n95% confidence intervals for ARR_DEL15 proportion by major airline")
        for carrier in major_airlines:
            subset = delay[delay["OP_UNIQUE_CARRIER"] == carrier]
            p_hat = subset["ARR_DEL15"].mean()
            n = len(subset)
            se = math.sqrt((p_hat * (1 - p_hat)) / n)
            z = 1.96
            ci_low = max(0.0, p_hat - z * se)
            ci_high = min(1.0, p_hat + z * se)
            result_lines.append(f"- {carrier}: rate {p_hat:.4f} 95% CI [{ci_low:.4f}, {ci_high:.4f}]")

    return "\n".join(result_lines)


def make_visualizations(operations: pd.DataFrame, delay: pd.DataFrame) -> None:
    plt.rcParams.update({"figure.dpi": 140, "font.size": 10})

    eligible_arrival = operations[(operations["CANCELLED"].fillna(0) == 0) & (operations["DIVERTED"].fillna(0) == 0) & operations["ARR_DELAY"].notna()]

    # 1. Distribution of ARR_DELAY
    arr_delay = eligible_arrival["ARR_DELAY"].dropna()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(arr_delay, bins=80, color="#4C78A8", edgecolor="black")
    ax.set_title("Distribution of Arrival Delay")
    ax.set_xlabel("Arrival Delay (minutes)")
    ax.set_ylabel("Frequency")
    ax.set_xlim(-60, 180)
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "arr_delay_distribution.png")
    plt.close(fig)

    # 2. Arrival delay rate by major airline
    major_airlines = delay.groupby("OP_UNIQUE_CARRIER").size()
    major_airlines = major_airlines[major_airlines >= 10000].index
    airline_rates = delay[delay["OP_UNIQUE_CARRIER"].isin(major_airlines)].groupby("OP_UNIQUE_CARRIER")["ARR_DEL15"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    airline_rates.plot(kind="bar", color="#F58518", ax=ax)
    ax.set_title("Arrival Delay Rate by Major Airline")
    ax.set_xlabel("Airline")
    ax.set_ylabel("Arrival Delay Rate")
    ax.set_ylim(0, 0.35)
    ax.set_yticklabels([f"{y:.0%}" for y in ax.get_yticks()])
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "arrival_delay_rate_by_airline.png")
    plt.close(fig)

    # 3. Arrival delay rate by scheduled departure hour
    hour_rates = delay.groupby("SCHEDULED_DEP_HOUR")["ARR_DEL15"].mean().sort_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    hour_rates.plot(kind="line", marker="o", color="#54A24B", ax=ax)
    ax.set_title("Arrival Delay Rate by Scheduled Departure Hour")
    ax.set_xlabel("Scheduled Departure Hour")
    ax.set_ylabel("Arrival Delay Rate")
    ax.set_ylim(0, 0.35)
    ax.set_yticklabels([f"{y:.0%}" for y in ax.get_yticks()])
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "arrival_delay_rate_by_hour.png")
    plt.close(fig)

    # 4. Arrival delay rate by day of week
    day_rates = delay.groupby("DAY_OF_WEEK")["ARR_DEL15"].mean().sort_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    day_rates.plot(kind="bar", color="#72B7B2", ax=ax)
    ax.set_title("Arrival Delay Rate by Day of Week")
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Arrival Delay Rate")
    ax.set_ylim(0, 0.35)
    ax.set_yticklabels([f"{y:.0%}" for y in ax.get_yticks()])
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "arrival_delay_rate_by_day.png")
    plt.close(fig)

    # 5. Top high-volume origin airports by delay rate
    origin_summary = (
        delay.groupby("ORIGIN")
        .agg(flight_count=("ARR_DEL15", "size"), arrival_delay_15_rate=("ARR_DEL15", "mean"))
        .reset_index()
    )
    origin_summary = origin_summary[origin_summary["flight_count"] >= 10000].sort_values("flight_count", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    origin_summary.plot(x="ORIGIN", y="arrival_delay_15_rate", kind="bar", color="#B279A2", ax=ax)
    ax.set_title("Arrival Delay Rate for High-Volume Origins")
    ax.set_xlabel("Origin Airport")
    ax.set_ylabel("Arrival Delay Rate")
    ax.set_ylim(0, 0.35)
    ax.set_yticklabels([f"{y:.0%}" for y in ax.get_yticks()])
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "origin_delay_rates.png")
    plt.close(fig)

    # 6. Delay-cause contribution chart
    cause_summary = delay_cause_summary(operations)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cause_summary.plot(x="cause", y="total_minutes", kind="bar", color="#C44E52", ax=ax)
    ax.set_title("Total Delay Minutes by Cause")
    ax.set_xlabel("Delay Cause")
    ax.set_ylabel("Total Minutes")
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "delay_cause_contribution.png")
    plt.close(fig)


def write_summary_text(overall: pd.DataFrame, airline_df: pd.DataFrame, origin_df: pd.DataFrame, dest_df: pd.DataFrame, route_df: pd.DataFrame, day_df: pd.DataFrame, hour_df: pd.DataFrame, block_df: pd.DataFrame, distance_df: pd.DataFrame, cause_summary: pd.DataFrame, stats_text: str) -> None:
    lines = []
    lines.append("Airline Operations Intelligence - EDA Summary")
    lines.append("=" * 60)
    lines.append("DESCRIPTIVE: January 2025 operational patterns are reported for this dataset only.")
    lines.append("STATISTICAL: Tests below assess association, not causation.")
    lines.append("BUSINESS INTERPRETATION: Results may inform operations planning and monitoring.")
    lines.append("")
    lines.append("Overall KPIs")
    for _, row in overall.iterrows():
        lines.append(f"- {row['metric']}: {row['value']}")
    lines.append("- Mean and median differ because arrival-delay values are right-skewed and a small number of large delays pull the mean upward more than the median.")
    lines.append("")
    lines.append("Top airline findings")
    lines.append(f"- Highest-volume airlines: {', '.join(airline_df.head(5)['carrier'].astype(str).tolist())}")
    lines.append(f"- Lowest arrival-delay-rate airlines: {', '.join(airline_df.sort_values('arrival_delay_15_rate').head(5)['carrier'].astype(str).tolist())}")
    lines.append(f"- Highest arrival-delay-rate airlines: {', '.join(airline_df.sort_values('arrival_delay_15_rate', ascending=False).head(5)['carrier'].astype(str).tolist())}")
    lines.append(f"- Lowest cancellation-rate airlines: {', '.join(airline_df.sort_values('cancellation_rate').head(5)['carrier'].astype(str).tolist())}")
    lines.append("")
    lines.append("Top airport findings")
    lines.append(f"- Highest-volume origins: {', '.join(origin_df.head(5)['airport'].astype(str).tolist())}")
    lines.append(f"- Highest-volume destinations: {', '.join(dest_df.head(5)['airport'].astype(str).tolist())}")
    lines.append("")
    lines.append("Top route findings")
    lines.append(f"- Highest-volume routes: {', '.join(route_df.head(5)['ROUTE'].astype(str).tolist())}")
    lines.append(f"- Most reliable high-volume routes: {', '.join(route_df.sort_values('arrival_delay_15_rate').head(5)['ROUTE'].astype(str).tolist())}")
    lines.append(f"- Highest-delay-risk high-volume routes: {', '.join(route_df.sort_values('arrival_delay_15_rate', ascending=False).head(5)['ROUTE'].astype(str).tolist())}")
    lines.append("")
    lines.append("Time pattern findings")
    lines.append(f"- Delay rates by day of week: {day_df.to_string(index=False)}")
    lines.append(f"- Delay rates by scheduled departure hour: {hour_df.head(10).to_string(index=False)}")
    lines.append(f"- Delay rates by time block: {block_df.to_string(index=False)}")
    lines.append("")
    lines.append("Distance findings")
    lines.append(distance_df.to_string(index=False))
    lines.append("")
    lines.append("Delay-cause findings")
    lines.append(cause_summary.to_string(index=False))
    lines.append("")
    lines.append("Statistical analysis")
    lines.append(stats_text)
    lines.append("")
    lines.append("Important limitation")
    lines.append("The current dataset contains January 2025 only, so results should not be generalized to annual or seasonal airline performance.")

    (ANALYSIS_DIR / "eda_summary.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    operations, delay = load_data()
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    overall = summarize_overall_kpis(operations, delay)
    save_csv(overall, "overall_kpis.csv")

    airline_df = airline_performance(operations, delay)
    save_csv(airline_df, "airline_performance.csv")

    origin_df = airport_performance(operations, delay, "ORIGIN")
    save_csv(origin_df, "origin_airport_performance.csv")

    dest_df = airport_performance(operations, delay, "DEST")
    save_csv(dest_df, "destination_airport_performance.csv")

    route_df = route_performance(operations, delay)
    save_csv(route_df, "route_performance.csv")

    day_df, hour_df, block_df = time_patterns(delay)
    save_csv(day_df, "delay_by_day_of_week.csv")
    save_csv(hour_df, "delay_by_hour.csv")
    save_csv(block_df, "delay_by_time_block.csv")

    distance_df = distance_analysis(operations, delay)
    save_csv(distance_df, "delay_by_distance.csv")

    cause_summary = delay_cause_summary(operations)
    save_csv(cause_summary, "delay_causes_summary.csv")

    stats_text = run_statistical_tests(delay)
    (ANALYSIS_DIR / "statistical_results.txt").write_text(stats_text, encoding="utf-8")

    make_visualizations(operations, delay)

    write_summary_text(overall, airline_df, origin_df, dest_df, route_df, day_df, hour_df, block_df, distance_df, cause_summary, stats_text)

    print("Created analysis outputs in", ANALYSIS_DIR)
    print("Created charts in", IMAGES_DIR)


if __name__ == "__main__":
    main()
