.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt
	cd frontend && npm install

pipeline:
	python3 load_data.py
	python3 analyze.py

dashboard:
	python3 dashboard.py