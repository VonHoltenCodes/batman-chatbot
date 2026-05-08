"""Comic Vine API enricher.

Pulls per-character canonical data from comicvine.gamespot.com:
  - image_url (super/medium thumbnail)
  - real_name
  - aliases  (newline-separated string in the API; we normalize to JSON)
  - deck     (short bio — single sentence)
  - first_appearance (issue name + cover_date when available)
  - api_url  (the canonical Comic Vine page)

API key is read from COMIC_VINE_API_KEY (loaded by batman_config from .env).

Rate limit: 200 requests/hour. We throttle to 1/18s by default → ~1 char per
20s in practice (one search request per character). The full 685-character
run takes ~3.5 hours; use --limit for partial runs.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import batman_config as cfg  # noqa: E402
from data_processor.enrichers.base import (  # noqa: E402
    Entity,
    RateLimiter,
    iter_entities,
    mark_status,
    open_db,
    write_enrichment,
)

log = logging.getLogger("enrichers.comic_vine")

SOURCE = "comic_vine"

API_BASE = "https://comicvine.gamespot.com/api"
USER_AGENT = "BatmanChatbot/2.0 (https://github.com/VonHoltenCodes/batman-chatbot; trentonvonholten@gmail.com)"

# Comic Vine policy: 200/hr → 1 req per 18s. Add safety margin.
THROTTLE_S = 19.0

# Resource type IDs Comic Vine uses internally — useful for cross-references.
RESOURCE_CHARACTER = 4005


_FANDOM_SUFFIX_RE = re.compile(r"\s*\([^)]+\)\s*$")


def _normalize_name(raw: str) -> str:
    return _FANDOM_SUFFIX_RE.sub("", raw.replace("_", " ").strip()).strip()


def _api_get(session: requests.Session, path: str, params: dict[str, Any]) -> Optional[dict]:
    if not cfg.COMIC_VINE_API_KEY:
        raise RuntimeError("COMIC_VINE_API_KEY is not set (check .env)")
    full_params = {"api_key": cfg.COMIC_VINE_API_KEY, "format": "json", **params}
    url = f"{API_BASE}/{path.lstrip('/')}"
    try:
        r = session.get(url, params=full_params, timeout=20)
    except requests.RequestException as exc:
        log.warning("network error %s: %s", path, exc)
        return None
    if r.status_code == 420 or r.status_code == 429:
        log.warning("Comic Vine rate-limited (%s) — backing off 60s", r.status_code)
        time.sleep(60)
        return None
    if r.status_code >= 400:
        log.warning("HTTP %s on %s", r.status_code, path)
        return None
    try:
        data = r.json()
    except ValueError:
        return None
    # Comic Vine returns status_code inside the JSON envelope.
    if data.get("status_code") != 1:
        log.warning("API status_code=%s error=%s", data.get("status_code"), data.get("error"))
        return None
    return data


def _search_character(session: requests.Session, name: str) -> Optional[dict]:
    """Return the best DC-publisher match, or None.

    `?filter=name:X` is exact-match. We try that first, then fall back to
    `/search/?query=` which is fuzzy.
    """
    fields = "id,name,real_name,aliases,deck,image,publisher,first_appeared_in_issue,site_detail_url"

    # Pass 1: exact-name filter
    data = _api_get(
        session,
        "characters/",
        {"filter": f"name:{name}", "field_list": fields, "limit": 25},
    )
    if data and data.get("results"):
        match = _pick_dc_match(data["results"])
        if match:
            return match

    # Pass 2: fuzzy search across all resources, filter to characters locally
    data = _api_get(
        session,
        "search/",
        {"query": name, "resources": "character", "limit": 25, "field_list": fields},
    )
    if data and data.get("results"):
        match = _pick_dc_match(data["results"])
        if match:
            return match
    return None


def _pick_dc_match(results: list[dict]) -> Optional[dict]:
    dc_results = [r for r in results if (r.get("publisher") or {}).get("name") == "DC Comics"]
    return dc_results[0] if dc_results else None


def _extract_fields(result: dict) -> dict[str, str | None]:
    image = (result.get("image") or {})
    image_url = (
        image.get("super_url") or image.get("medium_url") or image.get("thumb_url") or None
    )

    aliases = result.get("aliases") or ""
    aliases_list = [a.strip() for a in aliases.split("\n") if a.strip()]
    aliases_json = json.dumps(aliases_list) if aliases_list else None

    fa = result.get("first_appeared_in_issue") or {}
    if fa:
        fa_str = " ".join(filter(None, [fa.get("name"), fa.get("issue_number")])).strip() or None
    else:
        fa_str = None

    return {
        "image_url": image_url,
        "real_name": (result.get("real_name") or "").strip() or None,
        "aliases": aliases_json,
        "deck": (result.get("deck") or "").strip() or None,
        "first_appearance": fa_str,
        "api_url": result.get("site_detail_url"),
    }


def run(limit: int | None = None, force: bool = False) -> dict:
    if not cfg.COMIC_VINE_API_KEY:
        raise SystemExit("ERROR: COMIC_VINE_API_KEY is not set. Add it to .env.")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    limiter = RateLimiter(THROTTLE_S)

    stats = {"processed": 0, "enriched": 0, "missed": 0, "errors": 0}
    with open_db() as conn:
        for entity in iter_entities(conn, types=["character"], limit=limit):
            stats["processed"] += 1
            if not force:
                row = conn.execute(
                    "SELECT 1 FROM entity_enrichment WHERE entity_id=? AND entity_type=? AND source=? AND field='_status'",
                    (entity.id, entity.entity_type, SOURCE),
                ).fetchone()
                if row:
                    continue

            limiter.wait()
            try:
                match = _search_character(session, _normalize_name(entity.name))
            except Exception as exc:  # noqa: BLE001
                log.warning("search error %s: %s", entity.name, exc)
                stats["errors"] += 1
                continue

            if match:
                fields = _extract_fields(match)
                if any(v for v in fields.values()):
                    write_enrichment(conn, entity, SOURCE, fields)
                    mark_status(conn, entity, SOURCE, "ok")
                    stats["enriched"] += 1
                    if stats["enriched"] % 10 == 0:
                        print(f"  enriched {stats['enriched']} / processed {stats['processed']}")
                else:
                    mark_status(conn, entity, SOURCE, "miss")
                    stats["missed"] += 1
            else:
                mark_status(conn, entity, SOURCE, "miss")
                stats["missed"] += 1
            conn.commit()
    return stats


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=None, help="Cap processed entities (smoke test)")
    p.add_argument("--force", action="store_true", help="Re-enrich already-attempted entities")
    args = p.parse_args()

    print(f"🦇 Comic Vine enrichment (limit={args.limit}, force={args.force})")
    print(f"   throttle: 1 req per {THROTTLE_S}s — 200/hr Comic Vine limit")
    stats = run(limit=args.limit, force=args.force)
    print(f"\n=== DONE ===  processed={stats['processed']} enriched={stats['enriched']} "
          f"missed={stats['missed']} errors={stats['errors']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
