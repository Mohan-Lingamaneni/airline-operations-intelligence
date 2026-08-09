"""Run the SQL analytics scripts and export CSV results to data/processed/sql_results."""

from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "airline_operations.db"
SQL_DIR = PROJECT_ROOT / "sql"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "sql_results"


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    index = 0

    while index < len(sql_text):
        char = sql_text[index]
        next_char = sql_text[index + 1] if index + 1 < len(sql_text) else ""

        if char == "'" and not in_double_quote:
            if in_single_quote and next_char == "'":
                current.append(char)
                current.append(next_char)
                index += 2
                continue
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            index += 1
            continue

        current.append(char)
        index += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)

    return statements


def run_query(sql_path: Path) -> list[pd.DataFrame]:
    conn = sqlite3.connect(DB_PATH)
    sql_text = sql_path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql_text)
    results: list[pd.DataFrame] = []

    for statement in statements:
        if not statement.strip():
            continue
        results.append(pd.read_sql_query(statement, conn))

    conn.close()
    return results


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        results = run_query(sql_file)
        for index, df in enumerate(results, start=1):
            output_name = f"{sql_file.stem}_query_{index:02d}.csv"
            output_path = OUTPUT_DIR / output_name
            df.to_csv(output_path, index=False)
            print(f"Saved {output_path.name} with {len(df)} row(s)")


if __name__ == "__main__":
    main()
