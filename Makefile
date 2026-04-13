# =============================================================================
# Teiko Technical Assignment — Makefile
# Author: William McLain
# =============================================================================

.PHONY: setup pipeline dashboard

# Install all Python + Node dependencies
setup:
	pip install -r requirements.txt
	cd frontend && npm install

# Run full pipeline: initialize DB → load data → generate all outputs (Parts 1-4)
pipeline:
	python load_data.py
	python analyze.py

# Start FastAPI backend + React frontend dev server
dashboard:
	python dashboard.py