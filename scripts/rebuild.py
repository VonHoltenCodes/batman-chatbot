#!/usr/bin/env python3
"""Rebuild pipeline orchestrator.

Stages:
  scrape  : run all scrapers against fandom + new sources (slow, network heavy)
  merge   : combine per-source JSON into master_database/*.json
  import  : load master JSON into SQLite
  embed   : (Phase 3) build the ChromaDB vector index

Default `--stages import` re-imports from existing JSON without re-scraping.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import batman_config as cfg  # noqa: E402


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"  → {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def stage_scrape() -> None:
    """Re-scrape everything. Slow (rate-limited)."""
    print("\n=== STAGE: scrape ===")
    scraper_dir = REPO_ROOT / "scraper"
    for script in (
        "safe_scraper.py",
        "vehicle_scraper.py",
        "locations_scraper.py",
        "organizations_scraper.py",
        "storylines_scraper.py",
    ):
        path = scraper_dir / script
        if not path.exists():
            print(f"  (skip {script} — not found)")
            continue
        _run([sys.executable, str(path)], cwd=scraper_dir)


def stage_merge() -> None:
    """Combine per-source JSONs into master_database/*.json."""
    print("\n=== STAGE: merge ===")
    merge_script = REPO_ROOT / "data_processor" / "merge_all_data.py"
    if not merge_script.exists():
        print(f"  (skip — {merge_script} not found)")
        return
    _run([sys.executable, str(merge_script)], cwd=merge_script.parent)


def stage_import() -> None:
    """Load master JSON into SQLite (rebuilt from scratch each time)."""
    print("\n=== STAGE: import ===")
    cfg.ensure_dirs()
    if cfg.DB_PATH.exists():
        print(f"  removing existing {cfg.DB_PATH.name} for clean rebuild")
        cfg.DB_PATH.unlink()
    importer_script = REPO_ROOT / "database" / "import_data.py"
    _run([sys.executable, str(importer_script)], cwd=importer_script.parent)


def stage_embed() -> None:
    """Build ChromaDB vector index (Phase 3 — implemented later)."""
    print("\n=== STAGE: embed ===")
    embed_script = REPO_ROOT / "scripts" / "build_embeddings.py"
    if not embed_script.exists():
        print("  (skip — embeddings stage not yet implemented)")
        return
    _run([sys.executable, str(embed_script)])


STAGES = {
    "scrape": stage_scrape,
    "merge": stage_merge,
    "import": stage_import,
    "embed": stage_embed,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=list(STAGES.keys()) + ["all"],
        default=["import"],
        help="Which stages to run (default: import only)",
    )
    args = parser.parse_args()

    requested = list(STAGES.keys()) if "all" in args.stages else args.stages

    print(f"🦇 Rebuild pipeline starting: {requested}")
    t0 = time.time()
    for name in requested:
        STAGES[name]()
    print(f"\n✅ Done in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
