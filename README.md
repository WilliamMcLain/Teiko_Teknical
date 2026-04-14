# Teiko Technical — Clinical Cytometry Analysis Pipeline

A complete Python data pipeline and interactive dashboard for analyzing immune cell population dynamics in clinical trial data. Built for drug developer Bob Loblaw at Loblaw Bio to evaluate how the investigational drug miraclib affects immune cell populations in melanoma patients.

---

## Quick Start (GitHub Codespaces)

```bash
# 1. Install all dependencies
make setup

# 2. Run the full analysis pipeline (Parts 1-4)
make pipeline

# 3. Launch the interactive dashboard
make dashboard
```

Once `make dashboard` is running, open the **Ports** tab in Codespaces and click the globe icon next to port `5173`.

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### Environment Configuration

Create a `.env` file in the repo root:
```
CSV_FILE=data/cell-count.csv
DB_FILE=cell_counts.db
```

### Input Data
Place the provided `cell-count.csv` file in the `data/` folder:
```
data/
└── cell-count.csv
```

---

## Makefile Targets

| Target | What it does |
|---|---|
| `make setup` | Installs Python dependencies from `requirements.txt` and Node dependencies via `npm install` |
| `make pipeline` | Runs `load_data.py` (initialize DB + load CSV) then `analyze.py` (Parts 2-4 outputs) |
| `make dashboard` | Starts FastAPI backend on port 8000 and React frontend on port 5173 |

---

## Output Files

All outputs are written to a timestamped folder under `outputs/` on each pipeline run:

| File | Part | Description |
|---|---|---|
| `cell_counts.db` | 1 | SQLite database in repo root |
| `cell_frequencies_TIMESTAMP.csv` | 2 | Relative frequency of each cell population per sample |
| `responder_frequencies_TIMESTAMP.csv` | 3 | Frequencies for melanoma / miraclib / PBMC cohort by response |
| `responder_boxplots_TIMESTAMP.png` | 3 | Boxplot comparing responders vs non-responders |
| `baseline_cohort_TIMESTAMP.csv` | 4 | Baseline (time=0) subset for melanoma / miraclib / PBMC patients |

---

## Database Schema

### Design

```
projects
└── project_id  TEXT  PRIMARY KEY

subjects
├── subject_id  TEXT  PRIMARY KEY
├── project_id  TEXT  FK → projects
├── condition   TEXT
├── age         INTEGER
├── sex         TEXT
├── treatment   TEXT
└── response    TEXT

samples
├── sample_id                   TEXT  PRIMARY KEY
├── subject_id                  TEXT  FK → subjects
├── sample_type                 TEXT
└── time_from_treatment_start   INTEGER

cell_counts
├── cell_count_id  INTEGER  PRIMARY KEY AUTOINCREMENT
├── sample_id      TEXT     FK → samples (UNIQUE)
├── b_cell         INTEGER
├── cd8_t_cell     INTEGER
├── cd4_t_cell     INTEGER
├── nk_cell        INTEGER
└── monocyte       INTEGER
```

### Rationale

The schema is normalized into four tables reflecting the natural hierarchy of clinical trial data: **projects → subjects → samples → cell_counts**.

Subject-level attributes (age, sex, condition, treatment, response) are stored once in `subjects` rather than repeated on every sample row. This eliminates redundancy and prevents update anomalies — if a subject's response classification changes, there is exactly one row to update.

`cell_counts` is separated from `samples` to keep biological metadata (what the sample is, when it was taken) distinct from measurement data (what was counted). This makes it straightforward to add new assay types later without altering the samples table.

### How It Scales

| Scenario | How the schema handles it |
|---|---|
| Hundreds of projects | `projects` grows by one row per project. All joins remain indexed on primary keys |
| Thousands of subjects | `subjects` indexed on `subject_id` and `project_id`. Condition, treatment, sex can be indexed independently for fast cohort queries |
| Millions of samples | `samples` and `cell_counts` indexed on `sample_id`. `time_from_treatment_start` and `sample_type` can be added as composite indexes for time-series queries |
| New cell populations | Add a column to `cell_counts`. The `relative_frequency()` function accepts any list of column names — no hardcoded logic to update |
| New assay types | Add a new measurement table (e.g. `protein_counts`) linked to `samples` by `sample_id`. Existing schema is unaffected |
| Production scale | The normalized structure supports aggregation at any level. Moving from SQLite to PostgreSQL or DuckDB requires only a connection string change |

---

## Code Structure

```
.
├── load_data.py          # Part 1 — schema init and CSV loading
├── analyze.py            # Parts 2-4 — all analysis and outputs
├── dashboard.py          # Entry point — starts backend and frontend
├── backend/
│   └── main.py           # FastAPI server — /api/filters and /api/analyze
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main layout and group state
│   │   ├── api.ts            # Fetch wrappers
│   │   ├── types.ts          # TypeScript interfaces
│   │   └── components/
│   │       ├── GroupPanel.tsx    # Filter chips per group
│   │       ├── Charts.tsx        # Plotly histogram and boxplot
│   │       └── StatsTable.tsx    # Cohort summary and stats table
│   ├── package.json
│   └── vite.config.ts        # Proxies /api to localhost:8000
├── data/
│   └── cell-count.csv        # Input data
├── requirements.txt
├── Makefile
└── .env
```

### Design Decisions

**`load_data.py`** — single responsibility: schema initialization and CSV loading. Uses `INSERT OR IGNORE` so the script is safely re-runnable. All joins and deduplication happen in Python before any database writes.

**`analyze.py`** — the key design decision is `relative_frequency()` at the top — a single reusable abstraction that both Part 2 (all samples) and Part 3 (filtered cohort) call with different inputs. This guarantees the percentage calculation is identical across both analyses and eliminates code duplication.

**Why Polars** — columnar data processing with parallelism built in. The `unpivot` + vectorized division approach means zero Python loops over rows regardless of dataset size.

**Why Mann-Whitney U** — cell frequency percentages in flow cytometry are not normally distributed and often contain outliers. Mann-Whitney U makes no distributional assumptions and is robust to outliers, making it more appropriate than a t-test. Bonferroni correction is applied automatically when 3 or more groups are compared.

**Why FastAPI + React** — the dashboard requires dynamic group comparison with up to 4 user-defined cohorts. A Python backend runs all scipy and polars computation and serves JSON to a React frontend which renders interactive Plotly charts. This separation means the heavy computation stays in Python while the UI stays responsive.

**Filter discipline** — all cohort constraints are applied in SQL at load time to minimize memory usage, then re-enforced in the analysis functions themselves as a correctness guarantee.

---

## Technology Stack

| Component | Technology |
|---|---|
| Data Processing | Python, Polars |
| Database | SQLite3 |
| Statistics | SciPy (Mann-Whitney U) |
| Visualization | Matplotlib (pipeline), Plotly (dashboard) |
| Backend API | FastAPI, Uvicorn |
| Frontend | React 18, TypeScript, Vite |
| Automation | Makefile |

---

## Dashboard

The dashboard is accessible at `http://localhost:5173` after running `make dashboard`.

**Features:**
- Compare up to 4 user-defined cohorts simultaneously
- Filter each group independently by condition, treatment, sample type, sex, response, time point, and project
- Toggle between boxplot and histogram views
- Select any subset of cell populations to display
- Mann-Whitney U statistics with automatic Bonferroni correction for 3+ groups
- Cohort summary showing N samples and N subjects per group

**Dashboard link:** http://localhost:5173


**Statement of Appreciation:** 
- Lastly, I wanted to say thank you to the team at Teiko for taking the time to look into my application and this repository