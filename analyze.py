'''
Main: Teiko Technical Assignment
Sub: analyze.py

Author: William McLain
Date: 2026-04-12
Version: 4.0.0
'''

import sqlite3
import os
from datetime import datetime
import polars as pl
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.getenv("DB_FILE", "cell_counts.db")

CELL_POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

POPULATION_LABELS = {
    "b_cell":     "B Cell",
    "cd8_t_cell": "CD8 T Cell",
    "cd4_t_cell": "CD4 T Cell",
    "nk_cell":    "NK Cell",
    "monocyte":   "Monocyte",
}

# =============================================================================
# Core Abstraction: Relative Frequency
# =============================================================================

def relative_frequency(
    df: pl.DataFrame,
    populations: list[str] = CELL_POPULATIONS,
    extra_index: list[str] = [],
) -> pl.DataFrame:
    """
    Given a wide-format DataFrame with one row per sample and one column per
    cell population, return a long-format DataFrame with columns:
        sample, total_count, population, count, percentage
        (+ any columns listed in extra_index, e.g. ["response"])

    Works on any set of population columns passed in — not hardcoded to the
    five defaults — so it scales cleanly if new cell types are added later.

    extra_index lets callers thread additional metadata columns (like response
    or treatment) through the unpivot without duplicating any logic here.

    Polars executes all column operations in parallel and never loops in Python,
    keeping this fast regardless of dataset size.
    """
    index_cols  = ["sample_id", "total_count"] + extra_index
    output_cols = ["sample", "total_count"] + extra_index + ["population", "count", "percentage"]

    return (
        df
        .with_columns(
            pl.sum_horizontal(populations).alias("total_count")
        )
        .unpivot(
            on=populations,
            index=index_cols,
            variable_name="population",
            value_name="count",
        )
        .with_columns(
            ((pl.col("count") / pl.col("total_count")) * 100)
            .round(4)
            .alias("percentage")
        )
        .rename({"sample_id": "sample"})
        .select(output_cols)
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
# Part 3: Statistical Analysis — Responders vs Non-Responders
# =============================================================================

def load_melanoma_miraclib_pbmc(conn: sqlite3.Connection) -> pl.DataFrame:
    """
    Load wide-format cell counts enforcing all four constraints for Part 3:

        1. condition   = melanoma   — only melanoma patients
        2. treatment   = miraclib   — only patients receiving miraclib
        3. sample_type = PBMC       — biological sample type filter
        4. response IN (yes, no)    — must have a known response value;
                                      excludes healthy/control subjects who
                                      have NULL in the response column which is repetitive but its fine

    All filtering happens in SQL so only the relevant rows ever enter memory.
    """
    query = """
        SELECT
            sa.sample_id,
            su.response,
            cc.b_cell,
            cc.cd8_t_cell,
            cc.cd4_t_cell,
            cc.nk_cell,
            cc.monocyte
        FROM subjects su
        JOIN samples sa     ON su.subject_id = sa.subject_id
        JOIN cell_counts cc ON sa.sample_id  = cc.sample_id
        WHERE su.condition   = 'melanoma'          -- constraint 1
          AND su.treatment   = 'miraclib'          -- constraint 2
          AND sa.sample_type = 'PBMC'              -- constraint 3
          AND su.response    IN ('yes', 'no')      -- constraint 4
        ORDER BY sa.sample_id
    """
    return pl.read_database(query, conn)


def compare_responders(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Compute relative frequencies for each population split by response group,
    then run a Mann-Whitney U test per population.

    Mann-Whitney U is used over a t-test because:
      - We cannot assume normal distribution of cell frequency percentages
      - It is robust to outliers, which are common in clinical flow cytometry data
      - It tests whether one group tends to have higher values than the other
        without requiring equal variance

    Returns:
        freq_df   — long-format percentages with response column
        stats_df  — per-population test results with U statistic, p-value,
                    significance flag, and mean % for each group
    """
    # Reuse relative_frequency(), threading response through as extra metadata
    freq_df = relative_frequency(df, extra_index=["response"])

    # Run Mann-Whitney U per population
    stat_rows = []
    for pop in CELL_POPULATIONS:
        pop_df = freq_df.filter(pl.col("population") == pop)

        responders     = pop_df.filter(pl.col("response") == "yes")["percentage"].to_list()
        non_responders = pop_df.filter(pl.col("response") == "no")["percentage"].to_list()

        u_stat, p_value = stats.mannwhitneyu(
            responders, non_responders, alternative="two-sided"
        )

        stat_rows.append({
            "population":             pop,
            "mean_pct_responder":     round(sum(responders)     / len(responders),     4),
            "mean_pct_non_responder": round(sum(non_responders) / len(non_responders), 4),
            "u_statistic":            round(u_stat, 2),
            "p_value":                round(p_value, 6),
            "significant":            p_value < 0.05,
        })

    stats_df = pl.DataFrame(stat_rows)
    return freq_df, stats_df


def print_stats_table(stats_df: pl.DataFrame) -> None:
    """Print the statistical results table to the terminal."""
    print("\n[Part 3] Mann-Whitney U Test — Responders vs Non-Responders")
    print("(Melanoma | Miraclib | PBMC only)")
    print(stats_df)

    sig     = stats_df.filter(pl.col("significant") == True)["population"].to_list()
    not_sig = stats_df.filter(pl.col("significant") == False)["population"].to_list()

    print("\n--- Interpretation ---")
    if sig:
        print(f"Significant (p < 0.05): {', '.join(sig)}")
    if not_sig:
        print(f"Not significant:        {', '.join(not_sig)}")


def plot_boxplots(freq_df: pl.DataFrame, stats_df: pl.DataFrame, output_path: str) -> None:
    """
    Render a side-by-side boxplot for each cell population comparing
    responders vs non-responders, annotated with p-values.
    """
    n_pops = len(CELL_POPULATIONS)
    fig, axes = plt.subplots(1, n_pops, figsize=(4 * n_pops, 6), sharey=False)
    fig.suptitle(
        "Cell Population Frequencies: Responders vs Non-Responders\n"
        "(Melanoma | Miraclib | PBMC)",
        fontsize=13, fontweight="bold", y=1.01
    )

    COLORS = {"yes": "#2196F3", "no": "#F44336"}
    LABELS = {"yes": "Responder", "no": "Non-Responder"}

    for ax, pop in zip(axes, CELL_POPULATIONS):
        pop_df   = freq_df.filter(pl.col("population") == pop)
        yes_vals = pop_df.filter(pl.col("response") == "yes")["percentage"].to_list()
        no_vals  = pop_df.filter(pl.col("response") == "no")["percentage"].to_list()

        bp = ax.boxplot(
            [yes_vals, no_vals],
            patch_artist=True,
            widths=0.5,
            medianprops=dict(color="black", linewidth=2),
            flierprops=dict(marker="o", markersize=3, alpha=0.4),
        )

        for patch, key in zip(bp["boxes"], ["yes", "no"]):
            patch.set_facecolor(COLORS[key])
            patch.set_alpha(0.75)

        # Annotate p-value
        p_val   = stats_df.filter(pl.col("population") == pop)["p_value"][0]
        sig     = stats_df.filter(pl.col("population") == pop)["significant"][0]
        p_label = f"p = {p_val:.4f}" + (" *" if sig else "")
        ax.set_title(f"{POPULATION_LABELS[pop]}\n{p_label}", fontsize=10)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(["Responder", "Non-Resp."], fontsize=9)
        ax.set_ylabel("Relative Frequency (%)" if pop == CELL_POPULATIONS[0] else "")
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Shared legend
    patches = [mpatches.Patch(color=COLORS[k], alpha=0.75, label=LABELS[k]) for k in ["yes", "no"]]
    fig.legend(handles=patches, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.05), fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Exported: {output_path}")


# =============================================================================
# Part 4: Subset Analysis — Baseline Melanoma Miraclib PBMC Samples
# =============================================================================

def load_baseline_melanoma_miraclib_pbmc(conn: sqlite3.Connection) -> pl.DataFrame:
    """
    Load all melanoma PBMC samples at baseline (time_from_treatment_start = 0)
    from patients treated with miraclib.

    Constraints:
        1. condition              = melanoma
        2. treatment              = miraclib
        3. sample_type            = PBMC
        4. time_from_treatment_start = 0      — baseline only

    Pulls subject-level metadata (project, response, sex) alongside sample and
    cell count data so all downstream Part 4 summaries work from one query.
    """
    query = """
        SELECT
            sa.sample_id,
            su.project_id,
            su.subject_id,
            su.response,
            su.sex,
            cc.b_cell,
            cc.cd8_t_cell,
            cc.cd4_t_cell,
            cc.nk_cell,
            cc.monocyte
        FROM subjects su
        JOIN samples sa     ON su.subject_id = sa.subject_id
        JOIN cell_counts cc ON sa.sample_id  = cc.sample_id
        WHERE su.condition                = 'melanoma'  -- constraint 1
          AND su.treatment                = 'miraclib'  -- constraint 2
          AND sa.sample_type              = 'PBMC'      -- constraint 3
          AND sa.time_from_treatment_start = 0          -- constraint 4
        ORDER BY sa.sample_id
    """
    return pl.read_database(query, conn)


def summarize_baseline(df: pl.DataFrame) -> None:
    """
    Print three breakdowns of the baseline melanoma miraclib PBMC cohort:
        1. Sample count per project
        2. Subject count by response (responders vs non-responders)
        3. Subject count by sex (males vs females)

    Uses distinct subject counts for (2) and (3) because one subject
    can only appear once at baseline — but being explicit avoids any
    double-counting if the data ever changes.
    """
    print("\n[Part 4] Baseline Subset Analysis")
    print("(Melanoma | Miraclib | PBMC | time_from_treatment_start = 0)")
    print(f"Total baseline samples: {len(df)}")

    # --- 4.1 Samples per project ---
    samples_per_project = (
        df
        .group_by("project_id")
        .agg(pl.len().alias("sample_count"))
        .sort("project_id")
    )
    print("\n-- Samples per Project --")
    print(samples_per_project)

    # --- 4.2 Subjects by response ---
    subjects_by_response = (
        df
        .unique(subset=["subject_id"])
        .group_by("response")
        .agg(pl.len().alias("subject_count"))
        .sort("response")
    )
    print("\n-- Subjects by Response --")
    print(subjects_by_response)

    # --- 4.3 Subjects by sex ---
    subjects_by_sex = (
        df
        .unique(subset=["subject_id"])
        .group_by("sex")
        .agg(pl.len().alias("subject_count"))
        .sort("sex")
    )
    print("\n-- Subjects by Sex --")
    print(subjects_by_sex)


def avg_bcell_melanoma_male_responders(df: pl.DataFrame) -> float:
    """
    Among melanoma males at baseline (time=0), compute the average raw
    b_cell count for responders only.

    Expects df to already be the baseline cohort (melanoma | miraclib | PBMC
    | time=0) — filters applied on top:
        - sex      = M
        - response = yes

    Note: this operates on raw b_cell counts, not relative frequencies.
    Returns a float rounded to two decimal places.
    """
    avg = (
        df
        .filter(pl.col("sex")      == "M")
        .filter(pl.col("response") == "yes")
        .select(pl.col("b_cell").mean())
        .item()
    )
    return round(avg, 2)


def export_baseline_csv(df: pl.DataFrame, output_path: str) -> None:
    """Export the baseline cohort to CSV for external use."""
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

    # Create timestamped output directory: outputs/YYYYMMDD_HHMMSS/
    run_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir  = os.path.join(script_dir, "outputs", run_ts)
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output directory: {out_dir}")

    conn = sqlite3.connect(db_path)
    try:
        # --- Part 2 ---
        raw_df  = load_cell_counts(conn)
        freq_df = relative_frequency(raw_df)
        print_frequency_table(freq_df)
        export_frequency_csv(
            freq_df,
            os.path.join(out_dir, f"cell_frequencies_{run_ts}.csv")
        )

        # --- Part 3 ---
        melanoma_df            = load_melanoma_miraclib_pbmc(conn)
        resp_freq_df, stats_df = compare_responders(melanoma_df)
        print_stats_table(stats_df)
        export_frequency_csv(
            resp_freq_df.select(["sample", "response", "population", "count", "percentage"]),
            os.path.join(out_dir, f"responder_frequencies_{run_ts}.csv")
        )
        plot_boxplots(
            resp_freq_df, stats_df,
            os.path.join(out_dir, f"responder_boxplots_{run_ts}.png")
        )

        # --- Part 4 ---
        baseline_df = load_baseline_melanoma_miraclib_pbmc(conn)
        summarize_baseline(baseline_df)
        export_baseline_csv(
            baseline_df,
            os.path.join(out_dir, f"baseline_cohort_{run_ts}.csv")
        )

        avg_bcell = avg_bcell_melanoma_male_responders(baseline_df)
        print(f"\nAverage B Cell count for melanoma male responders at time=0: {avg_bcell:.2f}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()