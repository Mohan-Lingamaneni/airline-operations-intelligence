"""Initial inspection of the raw flight dataset.

This script is intentionally memory-conscious and limited to exploration.
It does not modify the raw data, create a cleaned dataset, or build models.
"""

from pathlib import Path

import pandas as pd


# Resolve the project root relative to this script so the notebook/script works
# regardless of the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "flights_2025_01.csv"


def main() -> None:
    """Load the CSV and print a concise initial inspection report."""
    print(f"Loading dataset from: {DATA_PATH}")

    # Load the CSV with pandas using a memory-conscious approach.
    # We keep the scope to inspection only and avoid any transformations.
    df = pd.read_csv(DATA_PATH)

    # Basic dataset shape.
    print("\nDataset shape:")
    print(df.shape)

    # Column names.
    print("\nColumn names:")
    for column in df.columns:
        print(f"- {column}")

    # Data types.
    print("\nData types:")
    print(df.dtypes)

    # Preview rows.
    print("\nFirst 5 rows:")
    print(df.head(5).to_string())

    # Missing values: counts and percentages.
    print("\nMissing values:")
    missing_count = df.isna().sum()
    missing_percent = (missing_count / len(df) * 100).round(2)
    missing_summary = pd.DataFrame({"missing_count": missing_count, "missing_percent": missing_percent})
    print(missing_summary[missing_summary["missing_count"] > 0].to_string())

    # Duplicate rows.
    duplicate_count = int(df.duplicated().sum())
    print(f"\nDuplicate row count: {duplicate_count}")

    # Numeric summary.
    print("\nNumeric descriptive statistics:")
    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        print(numeric_df.describe().to_string())
    else:
        print("No numeric columns found.")

    # Approximate memory usage.
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"\nApproximate memory usage: {memory_mb:.2f} MB")


if __name__ == "__main__":
    main()
