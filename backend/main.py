"""
Main: Teiko Technical Assignment
Sub: backend/main.py — FastAPI server

Author: William McLain
Date: 2026-04-12
Version: 1.0.0
"""

import os
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import polars as pl
from scipy import stats as scipy_stats
from dotenv import load_dotenv

# Load .env from repo root (one level up from backend/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

DB_FILE = os.getenv("DB_FILE", "cell_counts.db")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_FILE)

CELL_POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

GROUP_COLORS = ["#2196F3", "#FF9800", "#4CAF50", "#F44336"]  # Blue, Orange, Green, Red

app = FastAPI(title="Teiko Clinical Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Pydantic Models
# =============================================================================

class GroupFilter(BaseModel):
    label: str                          # e.g. "Group A"
    conditions: list[str]               # ["melanoma"], ["cancer"], ["healthy"], ["all"]
    treatments: list[str]               # ["miraclib"], ["phauximab"], ["drug"], ["all"]
    sample_types: list[str]             # ["PBMC"], ["WB"], ["all"]
    sexes: list[str]                    # ["M"], ["F"], ["all"]
    responses: list[str]                # ["yes"], ["no"], ["all"]
    time_points: list[str]              # ["0"], ["7"], ["14"], ["all"] — always strings, coerced in resolve
    projects: list[str]                 # ["prj1"], ["prj1+prj2"], ["all"]
    populations: list[str]              # subset of CELL_POPULATIONS


class AnalysisRequest(BaseModel):
    groups: list[GroupFilter]           # 1–4 groups


# =============================================================================
# Database helpers
# =============================================================================

def get_conn() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"Database not found at {DB_PATH}. Run `python load_data.py` first."
        )
    return sqlite3.connect(DB_PATH)


def build_query(f: GroupFilter) -> tuple[str, list]:
    """
    Build a parameterized SQL query for a given group filter.
    Returns (query_string, params_list).
    """
    placeholders = lambda lst: ",".join("?" * len(lst))

    query = f"""
        SELECT
            sa.sample_id,
            su.subject_id,
            su.project_id,
            su.condition,
            su.treatment,
            su.sex,
            su.response,
            sa.sample_type,
            sa.time_from_treatment_start,
            cc.b_cell,
            cc.cd8_t_cell,
            cc.cd4_t_cell,
            cc.nk_cell,
            cc.monocyte
        FROM subjects su
        JOIN samples sa     ON su.subject_id = sa.subject_id
        JOIN cell_counts cc ON sa.sample_id  = cc.sample_id
        WHERE su.condition                  IN ({placeholders(f.conditions)})
          AND su.treatment                  IN ({placeholders(f.treatments)})
          AND sa.sample_type                IN ({placeholders(f.sample_types)})
          AND su.sex                        IN ({placeholders(f.sexes)})
          AND sa.time_from_treatment_start  IN ({placeholders(f.time_points)})
          AND su.project_id                 IN ({placeholders(f.projects)})
    """
    # Coerce time_points to int here — they arrive as strings from the model
    time_points_int = [int(t) for t in f.time_points]

    params = (
        f.conditions
        + f.treatments
        + f.sample_types
        + f.sexes
        + time_points_int
        + f.projects
    )

    # Response is nullable — only filter if not requesting all
    if set(f.responses) != {"yes", "no"}:
        if "yes" in f.responses and "no" not in f.responses:
            query += " AND su.response = 'yes'"
        elif "no" in f.responses and "yes" not in f.responses:
            query += " AND su.response = 'no'"

    return query, params


def load_group(conn: sqlite3.Connection, f: GroupFilter) -> pl.DataFrame:
    """Execute the filter query and return a Polars DataFrame."""
    query, params = build_query(f)
    df = pl.read_database(query, conn, execute_options={"parameters": params})
    return df


def compute_relative_frequency(df: pl.DataFrame, populations: list[str]) -> pl.DataFrame:
    """
    Compute relative frequencies for selected populations.
    Total cell count is always across ALL five populations for clinical accuracy.
    """
    return (
        df
        .with_columns(
            pl.sum_horizontal(CELL_POPULATIONS).alias("total_count")
        )
        .unpivot(
            on=populations,
            index=["sample_id", "subject_id", "total_count"],
            variable_name="population",
            value_name="count",
        )
        .with_columns(
            ((pl.col("count") / pl.col("total_count")) * 100)
            .round(4)
            .alias("percentage")
        )
    )


# =============================================================================
# API Routes
# =============================================================================

@app.get("/api/health")
def health():
    return {"status": "ok", "db": DB_PATH}


@app.get("/api/filters")
def get_filter_options():
    """Return all available filter values for populating dropdowns."""
    return {
        "conditions": [
            {"value": "melanoma",             "label": "Melanoma"},
            {"value": "carcinoma",            "label": "Carcinoma"},
            {"value": "cancer",               "label": "Cancer (Melanoma + Carcinoma)"},
            {"value": "healthy",              "label": "Healthy"},
        ],
        "treatments": [
            {"value": "miraclib",             "label": "Miraclib"},
            {"value": "phauximab",            "label": "Phauximab"},
            {"value": "drug",                 "label": "Drug (Miraclib + Phauximab)"},
            {"value": "healthy",              "label": "Healthy (No Drug)"},
        ],
        "sample_types": [
            {"value": "PBMC",                 "label": "PBMC"},
            {"value": "WB",                   "label": "WB"},
        ],
        "sexes": [
            {"value": "M",                    "label": "Male"},
            {"value": "F",                    "label": "Female"},
        ],
        "responses": [
            {"value": "yes",                  "label": "Responders"},
            {"value": "no",                   "label": "Non-Responders"},
        ],
        "time_points": [
            {"value": "0",                    "label": "Baseline (0)"},
            {"value": "7",                    "label": "Week 1 (7)"},
            {"value": "14",                   "label": "Week 2 (14)"},
        ],
        "projects": [
            {"value": "prj1",                 "label": "Project 1"},
            {"value": "prj2",                 "label": "Project 2"},
            {"value": "prj3",                 "label": "Project 3"},
            {"value": "prj1+prj2",            "label": "Project 1 + 2"},
            {"value": "prj2+prj3",            "label": "Project 2 + 3"},
            {"value": "prj1+prj3",            "label": "Project 1 + 3"},
        ],
        "populations": [
            {"value": "b_cell",               "label": "B Cell"},
            {"value": "cd8_t_cell",           "label": "CD8 T Cell"},
            {"value": "cd4_t_cell",           "label": "CD4 T Cell"},
            {"value": "nk_cell",              "label": "NK Cell"},
            {"value": "monocyte",             "label": "Monocyte"},
        ],
    }


def resolve_filter(f: GroupFilter) -> GroupFilter:
    """
    Expand shorthand filter values (cancer, drug, all) into actual DB values.
    This keeps the API expressive without complicating the SQL builder.
    """
    # Conditions
    resolved_conditions = []
    for c in f.conditions:
        if c == "cancer":
            resolved_conditions += ["melanoma", "carcinoma"]
        else:
            resolved_conditions.append(c)

    # Treatments
    resolved_treatments = []
    for t in f.treatments:
        if t == "drug":
            resolved_treatments += ["miraclib", "phauximab"]
        elif t == "healthy":
            resolved_treatments.append("none")
        elif t == "all":
            resolved_treatments += ["miraclib", "phauximab", "none"]
        else:
            resolved_treatments.append(t)

    # Sample types
    resolved_sample_types = (
        ["PBMC", "WB"] if "all" in f.sample_types else f.sample_types
    )

    # Sexes
    resolved_sexes = (
        ["M", "F"] if "all" in f.sexes else f.sexes
    )

    # Responses
    resolved_responses = (
        ["yes", "no"] if "all" in f.responses else f.responses
    )

    # Time points — keep as strings in GroupFilter, coerce to int only in build_query
    if "all" in f.time_points:
        resolved_time_points = ["0", "7", "14"]
    else:
        resolved_time_points = [str(t) for t in f.time_points]

    # Projects
    resolved_projects = []
    for p in f.projects:
        if p == "all":
            resolved_projects += ["prj1", "prj2", "prj3"]
        elif "+" in p:
            resolved_projects += p.split("+")
        else:
            resolved_projects.append(p)

    return GroupFilter(
        label=f.label,
        conditions=list(set(resolved_conditions)),
        treatments=list(set(resolved_treatments)),
        sample_types=list(set(resolved_sample_types)),
        sexes=list(set(resolved_sexes)),
        responses=list(set(resolved_responses)),
        time_points=list(set(resolved_time_points)),
        projects=list(set(resolved_projects)),
        populations=f.populations,
    )


@app.post("/api/analyze")
def analyze(request: AnalysisRequest):
    """
    Core analysis endpoint. Accepts 1–4 group filters and returns:
        - histogram data (relative frequency distributions per population)
        - boxplot data (percentages per group per population)
        - stats table (Mann-Whitney U, Bonferroni-corrected p-values for 3+ groups)
        - cohort summary (N samples, N subjects per group)
    """
    if not 1 <= len(request.groups) <= 4:
        raise HTTPException(status_code=400, detail="Between 1 and 4 groups required.")

    # Validate each group has at least one value selected per field
    REQUIRED_FIELDS = {
        "conditions":   "Condition",
        "treatments":   "Treatment",
        "sample_types": "Sample Type",
        "sexes":        "Sex",
        "responses":    "Response",
        "time_points":  "Time Point",
        "projects":     "Project",
        "populations":  "Cell Population",
    }
    for group in request.groups:
        for field, label in REQUIRED_FIELDS.items():
            if not getattr(group, field):
                raise HTTPException(
                    status_code=400,
                    detail=f"Nothing selected for '{label}' in group '{group.label}'. Please select at least one option."
                )

    conn = get_conn()
    try:
        group_data = []
        for i, group_filter in enumerate(request.groups):
            resolved = resolve_filter(group_filter)
            df = load_group(conn, resolved)

            if len(df) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Group '{group_filter.label}' returned no samples. Adjust filters."
                )

            populations = resolved.populations if resolved.populations else CELL_POPULATIONS
            freq_df = compute_relative_frequency(df, populations)

            group_data.append({
                "filter":   resolved,
                "raw_df":   df,
                "freq_df":  freq_df,
                "color":    GROUP_COLORS[i],
                "label":    group_filter.label,
                "populations": populations,
            })

        # Collect all populations across groups
        all_populations = list(dict.fromkeys(
            pop for g in group_data for pop in g["populations"]
        ))

        # ── Cohort summary ──────────────────────────────────────────────────
        cohort_summary = []
        for g in group_data:
            df = g["raw_df"]
            cohort_summary.append({
                "group":      g["label"],
                "color":      g["color"],
                "n_samples":  len(df),
                "n_subjects": df["subject_id"].n_unique(),
            })

        # ── Histogram data ──────────────────────────────────────────────────
        histogram_data = []
        for pop in all_populations:
            pop_hist = {"population": pop, "groups": []}
            for g in group_data:
                pct_values = (
                    g["freq_df"]
                    .filter(pl.col("population") == pop)
                    ["percentage"]
                    .to_list()
                )
                pop_hist["groups"].append({
                    "label":      g["label"],
                    "color":      g["color"],
                    "values":     pct_values,
                })
            histogram_data.append(pop_hist)

        # ── Boxplot data ────────────────────────────────────────────────────
        boxplot_data = []
        for pop in all_populations:
            pop_box = {"population": pop, "groups": []}
            for g in group_data:
                pct_values = (
                    g["freq_df"]
                    .filter(pl.col("population") == pop)
                    ["percentage"]
                    .to_list()
                )
                sorted_vals = sorted(pct_values)
                n = len(sorted_vals)
                q1  = sorted_vals[n // 4]
                med = sorted_vals[n // 2]
                q3  = sorted_vals[(3 * n) // 4]
                iqr = q3 - q1
                pop_box["groups"].append({
                    "label":  g["label"],
                    "color":  g["color"],
                    "values": pct_values,
                    "q1":     round(q1,  4),
                    "median": round(med, 4),
                    "q3":     round(q3,  4),
                    "iqr":    round(iqr, 4),
                    "min":    round(max(sorted_vals[0],  q1 - 1.5 * iqr), 4),
                    "max":    round(min(sorted_vals[-1], q3 + 1.5 * iqr), 4),
                    "mean":   round(sum(pct_values) / len(pct_values), 4),
                })
            boxplot_data.append(pop_box)

        # ── Statistical tests ───────────────────────────────────────────────
        # Pairwise Mann-Whitney U across all group combinations
        # Apply Bonferroni correction when 3+ groups (multiple comparisons)
        from itertools import combinations
        n_groups = len(group_data)
        pairs = list(combinations(range(n_groups), 2))
        n_comparisons = len(pairs) * len(all_populations)
        apply_bonferroni = n_groups >= 3

        stats_rows = []
        for pop in all_populations:
            pop_group_vals = []
            for g in group_data:
                vals = (
                    g["freq_df"]
                    .filter(pl.col("population") == pop)
                    ["percentage"]
                    .to_list()
                )
                pop_group_vals.append(vals)

            for i, j in pairs:
                vals_i = pop_group_vals[i]
                vals_j = pop_group_vals[j]

                if len(vals_i) < 2 or len(vals_j) < 2:
                    continue

                u_stat, p_raw = scipy_stats.mannwhitneyu(
                    vals_i, vals_j, alternative="two-sided"
                )

                # Convert numpy scalars → Python native floats for JSON serialization
                u_stat = float(u_stat)
                p_raw  = float(p_raw)

                # Rank-biserial correlation — effect size
                n_i, n_j = len(vals_i), len(vals_j)
                effect_size = round(1 - (2 * u_stat) / (n_i * n_j), 4)

                p_corrected = float(min(p_raw * n_comparisons, 1.0)) if apply_bonferroni else None

                stats_rows.append({
                    "population":        pop,
                    "group_a":           group_data[i]["label"],
                    "group_b":           group_data[j]["label"],
                    "mean_a":            round(float(sum(vals_i) / len(vals_i)), 4),
                    "mean_b":            round(float(sum(vals_j) / len(vals_j)), 4),
                    "median_a":          round(float(sorted(vals_i)[len(vals_i) // 2]), 4),
                    "median_b":          round(float(sorted(vals_j)[len(vals_j) // 2]), 4),
                    "u_statistic":       round(u_stat, 2),
                    "p_value_raw":       round(p_raw, 6),
                    "p_value_corrected": round(p_corrected, 6) if p_corrected is not None else None,
                    "bonferroni_applied": apply_bonferroni,
                    "effect_size_rbc":   round(effect_size, 4),
                    "significant":       bool((p_corrected if apply_bonferroni else p_raw) < 0.05),
                })

        return {
            "cohort_summary": cohort_summary,
            "histogram_data": histogram_data,
            "boxplot_data":   boxplot_data,
            "stats":          stats_rows,
            "bonferroni_applied": apply_bonferroni,
            "n_comparisons":  n_comparisons if apply_bonferroni else None,
        }

    finally:
        conn.close()