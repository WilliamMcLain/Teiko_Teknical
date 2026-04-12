'''
Main: Teiko Technical Assignment
Sub: analyze.py

Author: William McLain
Date: 2026-04-12
Version: 2.0.0
'''

import sqlite3
import os
import polars as pl
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.getenv("DB_FILE", "cell_counts.db")

CELL_POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


# =============================================================================
# Core Abstraction: Relative Frequency
# =============================================================================

def relative_frequency(df: pl.DataFrame, populations: list[str] = CELL_POPULATIONS) -> pl.DataFrame:
    """
    Given a wide-format DataFrame with one row per sample and one column per
    cell population, return a long-format DataFrame with columns:
        sample, total_count, population, count, percentage

    Works on any set of population columns passed in — not hardcoded to the
    five defaults — so it scales cleanly if new cell types are added later.

    Polars executes all column operations in parallel and never loops in Python,
    keeping this fast regardless of dataset size.
    """
    return (
        df
        # Sum across all population columns to get total per sample
        .with_columns(
            pl.sum_horizontal(populations).alias("total_count")
        )
        # Pivot from wide (one col per population) to long (one row per population)
        .unpivot(
            on=populations,
            index=["sample_id", "total_count"],
            variable_name="population",
            value_name="count",
        )
        # Compute percentage in one vectorized pass
        .with_columns(
            ((pl.col("count") / pl.col("total_count")) * 100)
            .round(4)
            .alias("percentage")
        )
        .rename({"sample_id": "sample"})
        .select(["sample", "total_count", "population", "count", "percentage"])
        .sort(["sample", "population"])
    )


# =============================================================================
# Part 2: Cell Population Frequency Table
# =============================================================================

def load_cell_counts(conn: sqlite3.Connection) -> pl.DataFrame:
    """
    Pull the wide-format cell count table from SQLite into a Polars DataFrame.
    Joining here rather than in Python keeps memory usage low for large datasets.
    """
    query = """
        SELECT
            s.sample_id,
            cc.b_cell,
            cc.cd8_t_cell,
            cc.cd4_t_cell,
            cc.nk_cell,
            cc.monocyte
        FROM samples s
        JOIN cell_counts cc ON s.sample_id = cc.sample_id
        ORDER BY s.sample_id
    """
    return pl.read_database(query, conn)


def print_frequency_table(df: pl.DataFrame) -> None:
    """Print the frequency table to the terminal via Polars' built-in formatter."""
    print("\n[Part 2] Cell Population Relative Frequencies")
    print(df)
    print(f"Total rows: {len(df)}")


def export_frequency_csv(df: pl.DataFrame, output_path: str) -> None:
    """Write the frequency table to a CSV file."""
    df.write_csv(output_path)
    print(f"Exported: {output_path}")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path    = os.path.join(script_dir, DB_FILE)

    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "Run `python load_data.py` first to create it."
        )

    conn = sqlite3.connect(db_path)
    try:
        # --- Part 2 ---
        raw_df  = load_cell_counts(conn)
        freq_df = relative_frequency(raw_df)
        print_frequency_table(freq_df)
        export_frequency_csv(freq_df, os.path.join(script_dir, "cell_frequencies.csv"))

        # Parts 3 and 4 will be added here

    finally:
        conn.close()


if __name__ == "__main__":
    main()