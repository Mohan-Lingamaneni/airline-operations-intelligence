"""Data understanding and quality audit for the BTS flight dataset.

This script performs descriptive inspection only. It does not clean, impute,
or modify the dataset. It writes a metadata report to data/processed.
"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "flights_2025_01.csv"
REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "data_quality_report.csv"


def build_column_groups(df: pd.DataFrame) -> dict[str, list[str]]:
    """Group columns into logical categories when possible."""
    columns = list(df.columns)

    groups = {
        "Date/time": [c for c in columns if c in {"YEAR", "QUARTER", "MONTH", "DAY_OF_MONTH", "DAY_OF_WEEK", "FL_DATE"}],
        "Airline/carrier": [c for c in columns if c in {"OP_UNIQUE_CARRIER", "OP_CARRIER_AIRLINE_ID", "OP_CARRIER", "TAIL_NUM"}],
        "Origin/destination": [c for c in columns if c in {"ORIGIN_AIRPORT_ID", "ORIGIN_AIRPORT_SEQ_ID", "ORIGIN_CITY_MARKET_ID", "ORIGIN", "ORIGIN_CITY_NAME", "ORIGIN_STATE_ABR", "DEST_AIRPORT_ID", "DEST_AIRPORT_SEQ_ID", "DEST_CITY_MARKET_ID", "DEST", "DEST_CITY_NAME", "DEST_STATE_ABR", "DEST_STATE_NM"}],
        "Scheduled flight information": [c for c in columns if c in {"CRS_DEP_TIME", "CRS_ARR_TIME", "CRS_ELAPSED_TIME", "DEP_TIME_BLK", "ARR_TIME_BLK", "DISTANCE_GROUP", "FLIGHTS"}],
        "Actual flight information": [c for c in columns if c in {"DEP_TIME", "WHEELS_OFF", "WHEELS_ON", "TAXI_OUT", "TAXI_IN", "ARR_TIME", "ACTUAL_ELAPSED_TIME", "AIR_TIME"}],
        "Departure performance": [c for c in columns if c in {"DEP_DELAY", "DEP_DELAY_NEW", "DEP_DEL15", "DEP_DELAY_GROUP"}],
        "Arrival performance": [c for c in columns if c in {"ARR_DELAY", "ARR_DELAY_NEW", "ARR_DEL15", "ARR_DELAY_GROUP"}],
        "Cancellation/diversion": [c for c in columns if c in {"CANCELLED", "CANCELLATION_CODE", "DIVERTED"}],
        "Flight duration/distance": [c for c in columns if c in {"CRS_ELAPSED_TIME", "ACTUAL_ELAPSED_TIME", "AIR_TIME", "DISTANCE", "DISTANCE_GROUP"}],
        "Delay causes": [c for c in columns if c in {"CARRIER_DELAY", "WEATHER_DELAY", "NAS_DELAY", "SECURITY_DELAY", "LATE_AIRCRAFT_DELAY"}],
        "Other": [],
    }

    # Add any remaining columns to Other.
    assigned = set()
    for category_columns in groups.values():
        assigned.update(category_columns)
    groups["Other"] = [c for c in columns if c not in assigned]
    return groups


def create_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a compact data-quality summary for every column."""
    summary = pd.DataFrame(
        {
            "column_name": df.columns,
            "dtype": [str(dtype) for dtype in df.dtypes],
            "non_null_count": df.count().values,
            "missing_count": df.isna().sum().values,
            "missing_percentage": (df.isna().mean() * 100).round(2).values,
            "unique_values": [df[col].nunique(dropna=True) for col in df.columns],
        }
    )
    return summary


def print_categorical_profiles(df: pd.DataFrame) -> None:
    """Print compact value counts for several important categorical fields."""
    categorical_fields = [
        "OP_UNIQUE_CARRIER",
        "OP_CARRIER",
        "ORIGIN",
        "DEST",
        "CANCELLED",
        "DIVERTED",
        "CANCELLATION_CODE",
        "DEP_DEL15",
        "ARR_DEL15",
    ]

    for field in categorical_fields:
        if field in df.columns:
            print(f"\n{field} value counts:")
            counts = df[field].value_counts(dropna=False)
            print(counts.head(20).to_string())


def calculate_operational_metrics(df: pd.DataFrame) -> None:
    """Calculate descriptive operational counts without modifying the data."""
    print("\nOperational metrics")
    print("-" * 40)

    total_flights = len(df)
    print(f"Total flights: {total_flights}")

    completed_flights = int((df["CANCELLED"].fillna(0) == 0).sum()) if "CANCELLED" in df.columns else None
    print(f"Completed flights: {completed_flights} (missing values in CANCELLED were treated as 0 for this count)")

    cancelled_mask = df["CANCELLED"].fillna(0) == 1 if "CANCELLED" in df.columns else pd.Series([False] * len(df))
    cancelled_flights = int(cancelled_mask.sum())
    cancellation_rate = cancelled_flights / total_flights * 100 if total_flights else 0.0
    print(f"Cancelled flights: {cancelled_flights} ({cancellation_rate:.2f}%)")

    diverted_mask = df["DIVERTED"].fillna(0) == 1 if "DIVERTED" in df.columns else pd.Series([False] * len(df))
    diverted_flights = int(diverted_mask.sum())
    diversion_rate = diverted_flights / total_flights * 100 if total_flights else 0.0
    print(f"Diverted flights: {diverted_flights} ({diversion_rate:.2f}%)")

    dep_del15_mask = df["DEP_DEL15"].fillna(0) == 1 if "DEP_DEL15" in df.columns else pd.Series([False] * len(df))
    dep_del15_flights = int(dep_del15_mask.sum())
    print(f"Flights with departure delay >= 15 minutes: {dep_del15_flights} (missing DEP_DEL15 treated as 0 for this count)")

    arr_del15_mask = df["ARR_DEL15"].fillna(0) == 1 if "ARR_DEL15" in df.columns else pd.Series([False] * len(df))
    arr_del15_flights = int(arr_del15_mask.sum())
    print(f"Flights with arrival delay >= 15 minutes: {arr_del15_flights} (missing ARR_DEL15 treated as 0 for this count)")

    dep_delay_series = pd.to_numeric(df["DEP_DELAY"], errors="coerce") if "DEP_DELAY" in df.columns else pd.Series([pd.NA] * len(df))
    arr_delay_series = pd.to_numeric(df["ARR_DELAY"], errors="coerce") if "ARR_DELAY" in df.columns else pd.Series([pd.NA] * len(df))

    print("Average and median delay values are computed only from non-missing numeric values.")
    print(f"Average departure delay: {dep_delay_series.mean():.2f}")
    print(f"Median departure delay: {dep_delay_series.median():.2f}")
    print(f"Average arrival delay: {arr_delay_series.mean():.2f}")
    print(f"Median arrival delay: {arr_delay_series.median():.2f}")


def identify_leakage_columns(df: pd.DataFrame) -> None:
    """Classify columns by leakage risk for a pre-departure arrival-delay prediction task."""
    print("\nLeakage assessment for a pre-departure arrival-delay target")
    print("-" * 40)

    pre_departure = [
        "YEAR",
        "QUARTER",
        "MONTH",
        "DAY_OF_MONTH",
        "DAY_OF_WEEK",
        "FL_DATE",
        "OP_UNIQUE_CARRIER",
        "OP_CARRIER",
        "ORIGIN",
        "DEST",
        "CRS_DEP_TIME",
        "CRS_ARR_TIME",
        "CRS_ELAPSED_TIME",
        "DEP_TIME_BLK",
        "ARR_TIME_BLK",
        "DISTANCE",
        "DISTANCE_GROUP",
        "ORIGIN_AIRPORT_ID",
        "DEST_AIRPORT_ID",
        "ORIGIN_CITY_NAME",
        "DEST_CITY_NAME",
        "ORIGIN_STATE_ABR",
        "DEST_STATE_ABR",
    ]

    post_departure = [
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
    ]

    identifiers = [
        "OP_CARRIER_AIRLINE_ID",
        "OP_CARRIER_FL_NUM",
        "TAIL_NUM",
        "ORIGIN_AIRPORT_SEQ_ID",
        "ORIGIN_CITY_MARKET_ID",
        "DEST_AIRPORT_SEQ_ID",
        "DEST_CITY_MARKET_ID",
        "FLIGHTS",
    ]

    needs_investigation = [
        "CRS_DEP_TIME",
        "CRS_ARR_TIME",
        "DEP_TIME_BLK",
        "ARR_TIME_BLK",
        "FL_DATE",
    ]

    print("A. Potential pre-departure predictors")
    for col in pre_departure:
        if col in df.columns:
            print(f"- {col}")

    print("\nB. Post-departure / leakage variables")
    for col in post_departure:
        if col in df.columns:
            print(f"- {col}")

    print("\nC. Identifier/reference fields")
    for col in identifiers:
        if col in df.columns:
            print(f"- {col}")

    print("\nD. Needs further investigation")
    for col in needs_investigation:
        if col in df.columns:
            print(f"- {col}")


def main() -> None:
    """Run the audit flow and save the metadata report."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    print("Column groups")
    print("-" * 40)
    for name, columns in build_column_groups(df).items():
        print(f"{name}:")
        if columns:
            for col in columns:
                print(f"- {col}")
        else:
            print("- (none identified)")
        print()

    quality_summary = create_quality_summary(df)
    quality_summary.to_csv(REPORT_PATH, index=False)
    print(f"Saved data-quality summary to: {REPORT_PATH}")

    print("\nData-quality summary")
    print("-" * 40)
    print(quality_summary.to_string(index=False))

    print_categorical_profiles(df)
    calculate_operational_metrics(df)
    identify_leakage_columns(df)

    print("\nConcise audit report")
    print("-" * 40)
    print("Operational metrics: review the counts and rates above; all calculations used non-missing values where relevant and explicitly noted missing handling.")
    print("Important categorical observations: carrier, origin, destination, cancelled/diverted, and delay-flag fields should be reviewed for value consistency and potential category encoding decisions.")
    print("Data-quality issues requiring decisions: missingness in cancellation-related fields, delay-cause fields, and timing columns needs a manual policy decision before any modeling or cleaning.")
    print("Potential leakage columns: post-departure flight operations and delay outcome variables should be excluded from any pre-departure feature set.")
    print("Questions/decisions before cleaning: decide whether to treat missing values as informative, whether to encode categorical fields as strings or codes, and which columns should be preserved as identifiers versus features.")


if __name__ == "__main__":
    main()
