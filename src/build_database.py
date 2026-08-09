"""Build a local SQLite database from the processed flight CSV files."""

from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "airline_operations.db"
OPERATIONS_CSV = PROJECT_ROOT / "data" / "processed" / "flights_operations_2025_01.csv"
DELAY_CSV = PROJECT_ROOT / "data" / "processed" / "flights_delay_analysis_2025_01.csv"


def infer_sqlite_type(series: pd.Series) -> str:
    dtype = str(series.dtype)
    if "int" in dtype:
        return "INTEGER"
    if "float" in dtype:
        return "REAL"
    return "TEXT"


def create_table(cursor: sqlite3.Cursor, table_name: str, df: pd.DataFrame) -> None:
    columns_sql = []
    for col in df.columns:
        safe_col = col.replace("-", "_")
        safe_col = safe_col.replace(" ", "_")
        safe_col = safe_col.replace("/", "_")
        safe_col = safe_col.strip()
        columns_sql.append(f'"{safe_col}" {infer_sqlite_type(df[col])}')
    create_sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(columns_sql)})'
    cursor.execute(create_sql)


def load_csv_to_table(cursor: sqlite3.Cursor, table_name: str, csv_path: Path) -> int:
    df = pd.read_csv(csv_path)
    create_table(cursor, table_name, df)
    df.columns = [col.replace("-", "_").replace(" ", "_").replace("/", "_").strip() for col in df.columns]
    df.to_sql(table_name, cursor.connection, if_exists="replace", index=False)
    return len(df)


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    operations_rows = load_csv_to_table(cursor, "flights_operations", OPERATIONS_CSV)
    delay_rows = load_csv_to_table(cursor, "flights_delay_analysis", DELAY_CSV)

    conn.commit()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print("Created tables:", tables)
    print("flights_operations rows:", operations_rows)
    print("flights_delay_analysis rows:", delay_rows)

    conn.close()


if __name__ == "__main__":
    main()
