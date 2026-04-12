# Teiko Technical – Clinical Cytometry Analysis Pipeline

This repository contains a complete Python-based data pipeline and interactive dashboard for analyzing immune cell population dynamics in clinical trial data. Designed for drug developer Bob Loblaw at Loblaw Bio, the tool processes cell count data from PBMC samples to evaluate treatment effects of the investigational drug **miraclib** in melanoma patients.

---

## Key Features

### Relational Database Schema
SQLite-based design with proper normalization (projects → subjects → samples → cell_counts), supporting foreign key constraints and efficient querying at scale. Handles hundreds of projects and thousands of samples without redundancy.

### Data Loading
`load_data.py` initializes the database and loads `cell-count.csv` into a normalized schema with automatic type conversion and NULL handling.

### Frequency Analysis
Computes relative frequencies of five immune cell populations (B cells, CD8+ T cells, CD4+ T cells, NK cells, monocytes) per sample using vectorized operations via Polars.

### Statistical Comparison
Mann-Whitney U tests comparing responders vs. non-responders to miraclib in melanoma patients, with boxplot visualizations and p-value annotations.

### Subset Analysis
Query capabilities for baseline samples (time_from_treatment_start = 0) including:
- Sample counts per project
- Subject stratification by response (responder/non-responder)
- Subject stratification by sex (male/female)
- Average B cell count calculation for melanoma male responders

### Interactive Dashboard
Dash-based web interface for exploring cell population distributions, comparing response groups, and visualizing statistical results.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Data Processing | Python, Polars, Pandas |
| Database | SQLite3 |
| Statistics | SciPy (Mann-Whitney U) |
| Visualization | Matplotlib, Plotly |
| Dashboard | Dash |
| Automation | Makefile |

---

## Repository Structure

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/WilliamMcLain/Teiko_Teknical.git
cd Teiko_Teknical

# Install dependencies
make setup

# Run complete analysis pipeline
make pipeline

# Launch interactive dashboard
make dashboard
