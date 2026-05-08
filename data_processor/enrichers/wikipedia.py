"""Wikipedia enricher.

For each entity in the SQLite database, look up the matching Wikipedia
article via the public REST API and store: summary, canonical URL, and
(when present) the thumbnail image URL.

We use Wikipedia's REST `summary` endpoint which is purpose-built for this
and includes built-in disambiguation handling. Falls back to the action
API's `query` endpoint if `summary` 404s.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

# Make repo root importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data_processor.enrichers.base import (  # noqa: E402
    Entity,
    RateLimiter,
    iter_entities,
    mark_status,
    open_db,
    write_enrichment,
)

log = logging.getLogger("enrichers.wikipedia")

SOURCE = "wikipedia"

USER_AGENT = "BatmanChatbot/2.0 (https://github.com/VonHoltenCodes/batman-chatbot; trentonvonholten@gmail.com)"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

# Wikipedia is generous (200/s) but we go gentle.
THROTTLE_S = 0.2

_FANDOM_SUFFIX_RE = re.compile(r"\s*\([^)]+\)\s*$")


def _normalize_name(raw: str) -> str:
    """Fandom IDs use underscores and trailing media tags like '(Gotham)'."""
    name = raw.replace("_", " ").strip()
    # Strip the disambiguating suffix Fandom adds, e.g. "Aaron Helzinger (Gotham)".
    return _FANDOM_SUFFIX_RE.sub("", name).strip()


def _disambiguated_titles(entity: Entity) -> list[str]:
    base = _normalize_name(entity.name)
    candidates = [base]
    if entity.entity_type == "character":
        candidates += [
            f"{base} (character)",
            f"{base} (DC Comics)",
            f"{base} (comics)",
        ]
    elif entity.entity_type == "vehicle":
        candidates += [f"{base} (vehicle)", f"{base} (Batman)"]
    elif entity.entity_type == "location":
        candidates += [f"{base} (DC Comics)", f"{base} (Batman)"]
    elif entity.entity_type == "storyline":
        candidates += [f"{base} (comics)", f"{base} (storyline)"]
    elif entity.entity_type == "organization":
        candidates += [f"{base} (DC Comics)", f"{base} (comics)"]
    return candidates


def _fetch_summary(session: requests.Session, title: str) -> Optional[dict]:
    # Use safe="/" so '/' isn't encoded but special chars like apostrophes are.
    url_title = quote(title.replace(" ", "_"), safe="")
    url = SUMMARY_URL.format(title=url_title)
    try:
        r = session.get(url, timeout=10)
    except requests.RequestException as exc:
        log.warning("network error for %s: %s", title, exc)
        return None
    if r.status_code in (403, 404):
        return None
    if r.status_code == 429:
        log.warning("rate limited; backing off")
        time.sleep(2.0)
        return None
    if r.status_code >= 400:
        log.warning("HTTP %s for %s", r.status_code, title)
        return None
    try:
        data = r.json()
    except ValueError:
        return None
    if data.get("type") == "disambiguation":
        return None
    return data


def _looks_relevant(data: dict, entity: Entity) -> bool:
    """Heuristic: does this Wikipedia page actually describe THIS entity?

    Wikipedia's summary endpoint silently redirects misses to the nearest
    real article, so we have to check that the resulting article's title
    actually overlaps with the entity name — not just that it's Batman-ish.
    """
    title = str(data.get("title") or "").lower()
    extract = str(data.get("extract") or "").lower()
    description = str(data.get("description") or "").lower()
    blob = f"{title} {extract} {description}"

    # Hard rejects.
    if "marvel comics" in blob or "marvel cinematic" in blob:
        return False
    if title.startswith("list of") and len(extract) < 200:
        return False

    # Must look DC/Batman-adjacent.
    must_have_any = ("batman", "gotham", "dc comics", "wayne enterprises",
                     "wayne", "robin", "joker", "arkham", "supervillain",
                     "superhero", "vigilante", "dc universe", "dc extended")
    if not any(k in blob for k in must_have_any):
        return False

    # The article title or extract must reference at least one substantive
    # token from the entity name. Otherwise we've been redirected to a
    # generic page (e.g. "Bat-Sub" → the main "Batman" article).
    entity_name = _normalize_name(entity.name).lower()
    tokens = [t for t in re.split(r"[\s\-]+", entity_name) if len(t) > 2 and t not in {"the", "and", "of"}]
    if not tokens:
        return True  # one-word common name — give Wikipedia the benefit of the doubt
    haystack = f"{title} {extract[:400]}"
    return any(tok in haystack for tok in tokens)


def enrich_one(session: requests.Session, entity: Entity) -> dict[str, str | None]:
    for title in _disambiguated_titles(entity):
        data = _fetch_summary(session, title)
        if not data:
            continue
        if not _looks_relevant(data, entity):
            continue
        return {
            "summary": (data.get("extract") or "").strip() or None,
            "url": (data.get("content_urls", {}).get("desktop", {}).get("page")) or None,
            "image_url": (data.get("thumbnail", {}) or {}).get("source"),
            "wikidata_id": data.get("wikibase_item"),
        }
    return {}


def run(limit: int | None = None, types: list[str] | None = None, force: bool = False) -> dict:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    limiter = RateLimiter(THROTTLE_S)

    stats = {"processed": 0, "enriched": 0, "missed": 0, "errors": 0}
    with open_db() as conn:
        for entity in iter_entities(conn, types=types, limit=limit):
            stats["processed"] += 1
            if not force:
                # Skip if we have a summary already from this source
                row = conn.execute(
                    "SELECT 1 FROM entity_enrichment WHERE entity_id=? AND entity_type=? AND source=? AND field='summary'",
                    (entity.id, entity.entity_type, SOURCE),
                ).fetchone()
                if row:
                    continue

            limiter.wait()
            try:
                fields = enrich_one(session, entity)
            except Exception as exc:  # noqa: BLE001
                log.warning("error fetching %s: %s", entity.name, exc)
                stats["errors"] += 1
                continue

            if fields:
                write_enrichment(conn, entity, SOURCE, fields)
                mark_status(conn, entity, SOURCE, "ok")
                stats["enriched"] += 1
                if stats["enriched"] % 25 == 0:
                    print(f"  enriched {stats['enriched']} / processed {stats['processed']}")
            else:
                mark_status(conn, entity, SOURCE, "miss")
                stats["missed"] += 1
            conn.commit()
    return stats


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=None, help="Cap processed entities (smoke test)")
    p.add_argument("--types", nargs="*", default=None, help="Restrict to entity types")
    p.add_argument("--force", action="store_true", help="Re-enrich even if already done")
    args = p.parse_args()

    print(f"🦇 Wikipedia enrichment (limit={args.limit}, types={args.types}, force={args.force})")
    stats = run(limit=args.limit, types=args.types, force=args.force)
    print(f"\n=== DONE ===  processed={stats['processed']} enriched={stats['enriched']} "
          f"missed={stats['missed']} errors={stats['errors']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
