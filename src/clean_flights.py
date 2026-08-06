"""Reproducible cleaning and dataset creation for the BTS flight data.

This script performs a data-quality audit first, then creates two processed
outputs without modifying the raw CSV. It is intentionally limited to
metadata-driven cleaning decisions and interpretable feature engineering.
"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "flights_2025_01.csv"
OPERATIONS_OUT = PROJECT_ROOT / "data" / "processed" / "flights_operations_2025_01.csv"
DELAY_OUT = PROJECT_ROOT / "data" / "processed" / "flights_delay_analysis_2025_01.csv"
SUMMARY_OUT = PROJECT_ROOT / "data" / "processed" / "cleaning_summary.txt"


def _ensure_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def verify_missingness(df: pd.DataFrame) -> None:
    """Audit missingness patterns for cancellation and delay-cause fields."""
    print("Missingness validation")
    print("-" * 40)

    # 1) Missingness by cancellation status for actual departure/arrival fields.
    print("1. Missingness by CANCELLED status")
    fields = ["DEP_TIME", "DEP_DELAY", "DEP_DEL15", "ARR_TIME", "ARR_DELAY", "ARR_DEL15"]
    for field in fields:
        if field in df.columns:
            summary = (
                df.groupby("CANCELLED")[field]
                .apply(lambda s: pd.Series({"missing_count": int(s.isna().sum()), "missing_rate": round(s.isna().mean() * 100, 2)}))
                .unstack()
            )
            print(f"\n{field}")
            print(summary.to_string())

    # 2) Compare missingness in actual departure/arrival fields by cancellation status.
    print("\n2. Missingness explained by cancellation status")
    actual_fields = ["DEP_TIME", "DEP_DELAY", "ARR_TIME", "ARR_DELAY"]
    for field in actual_fields:
        if field in df.columns:
            cancelled_missing = df.loc[df["CANCELLED"].eq(1), field].isna().mean() * 100
            operated_missing = df.loc[df["CANCELLED"].eq(0), field].isna().mean() * 100
            print(f"{field}: cancelled missing {cancelled_missing:.2f}%, operated missing {operated_missing:.2f}%")

    # 3) Missingness by diversion status for arrival fields.
    print("\n3. Missingness by DIVERTED status")
    arrival_fields = ["ARR_TIME", "ARR_DELAY", "ARR_DEL15", "ACTUAL_ELAPSED_TIME"]
    for field in arrival_fields:
        if field in df.columns:
            summary = (
                df.groupby("DIVERTED")[field]
                .apply(lambda s: pd.Series({"missing_count": int(s.isna().sum()), "missing_rate": round(s.isna().mean() * 100, 2)}))
                .unstack()
            )
            print(f"\n{field}")
            print(summary.to_string())

    # 4) Delay-cause field availability by arrival-delay outcome and cancellation/diversion status.
    print("\n4. Availability of delay-cause fields")
    cause_fields = ["CARRIER_DELAY", "WEATHER_DELAY", "NAS_DELAY", "SECURITY_DELAY", "LATE_AIRCRAFT_DELAY"]
    groups = {
        "ARR_DELAY < 15": lambda d: d["ARR_DELAY"].notna() & d["ARR_DELAY"].lt(15),
        "ARR_DELAY >= 15": lambda d: d["ARR_DELAY"].notna() & d["ARR_DELAY"].ge(15),
        "CANCELLED": lambda d: d["CANCELLED"].eq(1),
        "DIVERTED": lambda d: d["DIVERTED"].eq(1),
    }
    for group_name, predicate in groups.items():
        mask = predicate(df)
        print(f"\nGroup: {group_name}")
        for field in cause_fields:
            if field in df.columns:
                available = (mask & df[field].notna()).sum()
                total = int(mask.sum())
                rate = round(available / total * 100, 2) if total else 0.0
                print(f"- {field}: {available}/{total} available ({rate:.2f}%)")


def create_operations_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Create the operations dataset with redundant or unnecessary columns removed."""
    removed_columns = []
    operations = df.copy()

    # Remove only clearly redundant or unnecessary columns.
    for col in ["OP_CARRIER_AIRLINE_ID", "FLIGHTS", "OP_CARRIER"]:
        if col in operations.columns:
            operations = operations.drop(columns=[col])
            removed_columns.append((col, "Redundant carrier identifier or uninformative column in operational analysis"))

    # Keep all scheduled flights, including cancelled/diverted flights.
    operations["FLIGHT_DATE"] = pd.to_datetime(operations["FL_DATE"], errors="coerce", format="mixed")
    operations["ROUTE"] = operations["ORIGIN"].fillna("") + "-" + operations["DEST"].fillna("")
    operations["SCHEDULED_DEP_HOUR"] = operations["CRS_DEP_TIME"].apply(_scheduled_hour)
    operations["SCHEDULED_ARR_HOUR"] = operations["CRS_ARR_TIME"].apply(_scheduled_hour)
    operations["DEP_TIME_BLOCK_CUSTOM"] = operations["SCHEDULED_DEP_HOUR"].apply(_time_block)

    return operations, removed_columns


def create_delay_analysis_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Create the delay-analysis dataset for operated flights with a valid target."""
    delay_df = df.copy()

    # Eligibility: operated flights and a non-missing ARR_DEL15 target.
    delay_df = delay_df.loc[
        delay_df["CANCELLED"].eq(0) & delay_df["DIVERTED"].eq(0) & delay_df["ARR_DEL15"].notna()
    ].copy()

    # Keep only pre-departure or non-leaky fields for the analysis dataset.
    keep_columns = [
        "YEAR",
        "QUARTER",
        "MONTH",
        "DAY_OF_MONTH",
        "DAY_OF_WEEK",
        "FL_DATE",
        "FLIGHT_DATE",
        "OP_UNIQUE_CARRIER",
        "ORIGIN",
        "DEST",
        "ROUTE",
        "CRS_DEP_TIME",
        "SCHEDULED_DEP_HOUR",
        "DEP_TIME_BLOCK_CUSTOM",
        "CRS_ARR_TIME",
        "SCHEDULED_ARR_HOUR",
        "ARR_TIME_BLK",
        "CRS_ELAPSED_TIME",
        "DISTANCE",
        "DISTANCE_GROUP",
        "ORIGIN_AIRPORT_ID",
        "ORIGIN_CITY_NAME",
        "ORIGIN_STATE_ABR",
        "DEST_AIRPORT_ID",
        "DEST_CITY_NAME",
        "DEST_STATE_ABR",
        "OP_CARRIER_FL_NUM",
        "TAIL_NUM",
        "ARR_DEL15",
    ]

    # Some columns may be absent because they were removed earlier; keep only those present.
    keep_columns = [c for c in keep_columns if c in delay_df.columns]
    delay_df = delay_df.loc[:, keep_columns].copy()

    return delay_df


def _scheduled_hour(value: object) -> int:
    if pd.isna(value):
        return pd.NA
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return pd.NA
    return int(str(number).zfill(4)[:2])


def _time_block(hour: object) -> str:
    if pd.isna(hour):
        return pd.NA
    try:
        hour_value = int(hour)
    except (TypeError, ValueError):
        return pd.NA
    if 0 <= hour_value <= 4:
        return "Early Morning"
    if 5 <= hour_value <= 11:
        return "Morning"
    if 12 <= hour_value <= 16:
        return "Afternoon"
    if 17 <= hour_value <= 20:
        return "Evening"
    return "Late Night"


def validate_datasets(operations: pd.DataFrame, delay_df: pd.DataFrame) -> dict[str, object]:
    """Validate dataset contents and return a summary dictionary."""
    validation = {}
    validation["operations_rows"] = len(operations)
    validation["operations_columns"] = operations.shape[1]
    validation["cancelled_count"] = int(operations["CANCELLED"].eq(1).sum())
    validation["cancelled_rate"] = round(validation["cancelled_count"] / len(operations) * 100, 2)
    validation["diverted_count"] = int(operations["DIVERTED"].eq(1).sum())
    validation["diverted_rate"] = round(validation["diverted_count"] / len(operations) * 100, 2)
    validation["delay_rows"] = len(delay_df)
    validation["delay_columns"] = delay_df.shape[1]
    validation["arr_del15_counts"] = delay_df["ARR_DEL15"].value_counts(dropna=False).to_dict()
    validation["arr_del15_percentages"] = round(delay_df["ARR_DEL15"].value_counts(dropna=False, normalize=True) * 100, 2).to_dict()
    validation["cancelled_in_delay_dataset"] = int(delay_df["CANCELLED"].eq(1).sum()) if "CANCELLED" in delay_df.columns else 0
    validation["diverted_in_delay_dataset"] = int(delay_df["DIVERTED"].eq(1).sum()) if "DIVERTED" in delay_df.columns else 0
    validation["missing_arr_del15"] = int(delay_df["ARR_DEL15"].isna().sum())
    validation["duplicate_rows_operations"] = int(operations.duplicated().sum())
    validation["duplicate_rows_delay"] = int(delay_df.duplicated().sum())
    validation["negative_distance"] = int((operations["DISTANCE"].fillna(0) < 0).sum()) if "DISTANCE" in operations.columns else 0
    validation["invalid_scheduled_times"] = int((operations["CRS_DEP_TIME"].fillna(0) < 0).sum() + (operations["CRS_ARR_TIME"].fillna(0) < 0).sum()) if {"CRS_DEP_TIME", "CRS_ARR_TIME"}.issubset(operations.columns) else 0
    validation["unexpected_cancelled_values"] = sorted({value for value in operations["CANCELLED"].dropna().unique().tolist() if value not in {0, 1}}) if "CANCELLED" in operations.columns else []
    validation["unexpected_diverted_values"] = sorted({value for value in operations["DIVERTED"].dropna().unique().tolist() if value not in {0, 1}}) if "DIVERTED" in operations.columns else []
    validation["unexpected_arr_del15_values"] = sorted({value for value in delay_df["ARR_DEL15"].dropna().unique().tolist() if value not in {0, 1}}) if "ARR_DEL15" in delay_df.columns else []
    validation["missing_route"] = int(operations["ROUTE"].isna().sum() + (operations["ROUTE"].eq("").sum())) if "ROUTE" in operations.columns else 0
    return validation


def write_summary_file(summary: dict[str, object], removed_columns: list[tuple[str, str]], feature_policy: dict[str, list[str]]) -> None:
    """Write a text summary of the cleaning decisions and outputs."""
    lines = []
    lines.append("Airline Operations Intelligence - Cleaning Summary")
    lines.append("=" * 60)
    lines.append(f"Original row count: {summary['original_rows']}")
    lines.append(f"Operations dataset rows: {summary['operations_rows']}")
    lines.append(f"Delay-analysis dataset rows: {summary['delay_rows']}")
    lines.append("")
    lines.append("Rows excluded from delay-analysis dataset")
    lines.append("- CANCELLED = 1")
    lines.append("- DIVERTED = 1")
    lines.append("- ARR_DEL15 missing")
    lines.append("")
    lines.append("Columns removed")
    for col, reason in removed_columns:
        lines.append(f"- {col}: {reason}")
    lines.append("")
    lines.append("Engineered fields")
    lines.append("- FLIGHT_DATE: parsed from FL_DATE")
    lines.append("- ROUTE: ORIGIN-DEST")
    lines.append("- SCHEDULED_DEP_HOUR: derived from CRS_DEP_TIME")
    lines.append("- SCHEDULED_ARR_HOUR: derived from CRS_ARR_TIME")
    lines.append("- DEP_TIME_BLOCK_CUSTOM: categorized from scheduled departure hour")
    lines.append("")
    lines.append("Missing-value decisions")
    lines.append("- Raw missing values were not filled or imputed.")
    lines.append("- Delay-cause columns were preserved as-is; no zero-fill applied.")
    lines.append("- ARR_DEL15 was used as target only for operated flights with a non-missing outcome.")
    lines.append("")
    lines.append("Leakage policy")
    lines.append("- Post-departure and outcome variables were excluded from the delay-analysis feature set.")
    lines.append("- ARR_DEL15 was retained as the target only.")
    lines.append("")
    lines.append("Feature policy")
    lines.append("Pre-departure candidate features:")
    for col in feature_policy["pre_departure"]:
        lines.append(f"- {col}")
    lines.append("Leakage/post-outcome variables:")
    for col in feature_policy["leakage"]:
        lines.append(f"- {col}")
    lines.append("Identifier/reference fields:")
    for col in feature_policy["identifiers"]:
        lines.append(f"- {col}")
    lines.append("")
    lines.append("Unresolved data-quality issues")
    lines.append("- A small number of records still have ambiguous or missing scheduled-time and route context values.")
    lines.append("- Delay-cause fields remain structurally sparse and should be reviewed manually before any inferential use.")

    SUMMARY_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    """Run the full audit and create the processed datasets."""
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_DATA_PATH)

    verify_missingness(df)

    operations, removed_columns = create_operations_dataset(df)
    operations.to_csv(OPERATIONS_OUT, index=False)

    delay_df = create_delay_analysis_dataset(operations)
    delay_df.to_csv(DELAY_OUT, index=False)

    feature_policy = {
        "pre_departure": [
            "MONTH",
            "DAY_OF_MONTH",
            "DAY_OF_WEEK",
            "OP_UNIQUE_CARRIER",
            "ORIGIN",
            "DEST",
            "CRS_DEP_TIME",
            "SCHEDULED_DEP_HOUR",
            "DEP_TIME_BLOCK_CUSTOM",
            "CRS_ARR_TIME",
            "SCHEDULED_ARR_HOUR",
            "ARR_TIME_BLK",
            "CRS_ELAPSED_TIME",
            "DISTANCE",
            "DISTANCE_GROUP",
        ],
        "leakage": [
            "DEP_TIME",
            "DEP_DELAY",
            "DEP_DELAY_NEW",
            "DEP_DEL15",
            "DEP_DELAY_GROUP",
            "TAXI_OUT",
            "WHEELS_OFF",
            "WHEELS_ON",
            "TAXI_IN",
            "ARR_TIME",
            "ARR_DELAY",
            "ARR_DELAY_NEW",
            "ARR_DEL15",
            "ARR_DELAY_GROUP",
            "ACTUAL_ELAPSED_TIME",
            "AIR_TIME",
            "CANCELLED",
            "CANCELLATION_CODE",
            "DIVERTED",
            "CARRIER_DELAY",
            "WEATHER_DELAY",
            "NAS_DELAY",
            "SECURITY_DELAY",
            "LATE_AIRCRAFT_DELAY",
        ],
        "identifiers": [
            "OP_CARRIER_FL_NUM",
            "TAIL_NUM",
            "ORIGIN_AIRPORT_ID",
            "DEST_AIRPORT_ID",
            "ORIGIN_CITY_NAME",
            "DEST_CITY_NAME",
            "ORIGIN_STATE_ABR",
            "DEST_STATE_ABR",
        ],
    }

    validation = validate_datasets(operations, delay_df)
    validation["original_rows"] = len(df)
    write_summary_file(validation, removed_columns, feature_policy)

    print("\nProcessed datasets")
    print("-" * 40)
    print(f"Operations dataset saved to: {OPERATIONS_OUT}")
    print(f"Delay-analysis dataset saved to: {DELAY_OUT}")
    print(f"Cleaning summary saved to: {SUMMARY_OUT}")

    print("\nValidation summary")
    print("-" * 40)
    print(f"Operations rows: {validation['operations_rows']}")
    print(f"Operations columns: {validation['operations_columns']}")
    print(f"Cancelled count/rate: {validation['cancelled_count']} / {validation['cancelled_rate']:.2f}%")
    print(f"Diverted count/rate: {validation['diverted_count']} / {validation['diverted_rate']:.2f}%")
    print(f"Delay-analysis rows: {validation['delay_rows']}")
    print(f"Delay-analysis columns: {validation['delay_columns']}")
    print(f"ARR_DEL15 class counts: {validation['arr_del15_counts']}")
    print(f"ARR_DEL15 class percentages: {validation['arr_del15_percentages']}")
    print(f"Cancelled flights in delay-analysis dataset: {validation['cancelled_in_delay_dataset']}")
    print(f"Diverted flights in delay-analysis dataset: {validation['diverted_in_delay_dataset']}")
    print(f"Missing ARR_DEL15 in delay-analysis dataset: {validation['missing_arr_del15']}")
    print(f"Duplicate rows (operations): {validation['duplicate_rows_operations']}")
    print(f"Duplicate rows (delay-analysis): {validation['duplicate_rows_delay']}")
    print(f"Negative DISTANCE rows: {validation['negative_distance']}")
    print(f"Invalid scheduled time rows: {validation['invalid_scheduled_times']}")
    print(f"Unexpected CANCELLED values: {validation['unexpected_cancelled_values']}")
    print(f"Unexpected DIVERTED values: {validation['unexpected_diverted_values']}")
    print(f"Unexpected ARR_DEL15 values: {validation['unexpected_arr_del15_values']}")
    print(f"Missing ROUTE values: {validation['missing_route']}")


if __name__ == "__main__":
    main()
