.PHONY: help install rebuild rebuild-all serve test fmt clean

PY ?= python3

help:
	@echo "Targets:"
	@echo "  install      Install Python deps from requirements.txt"
	@echo "  rebuild      Re-import existing JSON into SQLite"
	@echo "  rebuild-all  Full pipeline: scrape + merge + import + embed (slow)"
	@echo "  serve        Run the Flask web UI on :5001"
	@echo "  test         Run pytest suite"
	@echo "  fmt          Run ruff check + format (best-effort)"
	@echo "  clean        Remove caches, runtime sessions DB, chroma index"

install:
	$(PY) -m pip install -r requirements.txt

rebuild:
	$(PY) scripts/rebuild.py --stages import

rebuild-all:
	$(PY) scripts/rebuild.py --stages all

serve:
	$(PY) start_batman.py

test:
	$(PY) -m pytest -q

fmt:
	-$(PY) -m ruff check --fix .
	-$(PY) -m ruff format .

clean:
	rm -rf __pycache__ .pytest_cache **/__pycache__
	rm -f database/sessions.db database/sessions.db-*
	rm -rf database/chroma
