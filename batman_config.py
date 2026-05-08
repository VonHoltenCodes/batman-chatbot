"""Centralized paths and config for the Batman chatbot.

All paths derive from this file's location, so the project works regardless of cwd.
Environment variables (e.g. COMIC_VINE_API_KEY) are loaded from .env if present.
"""
from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent

# Data + database
DATABASE_DIR = REPO_ROOT / "database"
DB_PATH = DATABASE_DIR / "batman_universe.db"

MASTER_DB_DIR = REPO_ROOT / "data_processor" / "master_database"
SCRAPER_DATA_DIR = REPO_ROOT / "scraper" / "data"

# Phase 3 (embeddings)
CHROMA_DIR = REPO_ROOT / "database" / "chroma"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Web
SESSION_DB_PATH = DATABASE_DIR / "sessions.db"
SESSION_TTL_SECONDS = 60 * 60 * 24  # 24h

# Logs
LOG_DIR = REPO_ROOT / "logs"


def _load_dotenv() -> None:
    """Minimal .env loader (no python-dotenv dependency)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


_load_dotenv()


# Secrets / API keys (read after dotenv load)
COMIC_VINE_API_KEY = os.environ.get("COMIC_VINE_API_KEY", "")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "batcave_dev_only_replace_in_prod")


def ensure_dirs() -> None:
    """Create runtime directories that may not exist yet."""
    for d in (DATABASE_DIR, CHROMA_DIR, LOG_DIR, MASTER_DB_DIR, SCRAPER_DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)
