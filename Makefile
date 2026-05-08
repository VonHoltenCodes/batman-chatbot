.PHONY: help install rebuild rebuild-all enrich enrich-wikipedia enrich-comic-vine embed serve test fmt clean

PY ?= python3

help:
	@echo "Targets:"
	@echo "  install      Install Python deps from requirements.txt"
	@echo "  rebuild      Re-import existing JSON into SQLite"
	@echo "  rebuild-all  Full pipeline: scrape + merge + import + embed (slow)"
	@echo "  enrich       Run all source enrichers (Wikipedia, Comic Vine)"
	@echo "  enrich-wikipedia    Wikipedia only (fast)"
	@echo "  enrich-comic-vine   Comic Vine only (slow — 200/hr API limit, ~3.5h for full DB)"
	@echo "  embed        (Re)build the ChromaDB embeddings index (~40s on CPU)"
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

enrich: enrich-wikipedia enrich-comic-vine

enrich-wikipedia:
	$(PY) -m data_processor.enrichers.wikipedia

# Throttled to 200/hr — full 685-character run takes ~3.5 hours.
# Use `make enrich-comic-vine LIMIT=50` to process the first 50 instead.
LIMIT ?=
enrich-comic-vine:
	$(PY) -m data_processor.enrichers.comic_vine $(if $(LIMIT),--limit $(LIMIT))

embed:
	$(PY) scripts/build_embeddings.py --rebuild

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
