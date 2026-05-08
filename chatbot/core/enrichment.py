"""Read-through helper for the entity_enrichment table.

Given an entity row already loaded from `characters` / `vehicles` / etc.,
attach a nested `enrichment` dict containing per-source fields:

    {
        "wikipedia": {"summary": "...", "url": "...", "image_url": "..."},
        "comic_vine": {"deck": "...", "real_name": "...", "image_url": "...", ...},
    }

Plus convenience top-level fields the response templates can read directly
without knowing about sources:
    image_url        — best available thumbnail (Comic Vine > Wikipedia)
    overview         — short 1-2 sentence summary (Wikipedia preferred)
    canonical_name   — Comic Vine real_name when present
"""
from __future__ import annotations

import sqlite3
from typing import Any


# Maps the chatbot's table-derived entity type names to entity_enrichment.entity_type.
TABLE_TO_TYPE = {
    "characters": "character",
    "vehicles": "vehicle",
    "locations": "location",
    "storylines": "storyline",
    "organizations": "organization",
    # Already-singular forms used elsewhere in the chatbot
    "character": "character",
    "vehicle": "vehicle",
    "location": "location",
    "storyline": "storyline",
    "organization": "organization",
}


def fetch_enrichment(conn: sqlite3.Connection, entity_id: str, entity_type: str) -> dict[str, dict[str, str]]:
    """Return {source: {field: value}} for one entity, excluding bookkeeping fields."""
    etype = TABLE_TO_TYPE.get(entity_type, entity_type)
    rows = conn.execute(
        """
        SELECT source, field, value
        FROM entity_enrichment
        WHERE entity_id = ? AND entity_type = ? AND field != '_status'
        """,
        (entity_id, etype),
    ).fetchall()
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        # row may be a Row or tuple depending on conn.row_factory
        try:
            source, field, value = row["source"], row["field"], row["value"]
        except (TypeError, IndexError):
            source, field, value = row[0], row[1], row[2]
        if value is None:
            continue
        out.setdefault(source, {})[field] = value
    return out


def attach(entity: dict[str, Any], conn: sqlite3.Connection, entity_type: str) -> dict[str, Any]:
    """Mutate `entity` in place to add `enrichment`, `image_url`, `overview`, `canonical_name`."""
    if not entity or not entity.get("id"):
        return entity
    enrich = fetch_enrichment(conn, entity["id"], entity_type)
    if not enrich:
        return entity

    entity["enrichment"] = enrich

    # Convenience derivations — Comic Vine images tend to be higher quality.
    cv = enrich.get("comic_vine", {})
    wp = enrich.get("wikipedia", {})

    image_url = cv.get("image_url") or wp.get("image_url")
    if image_url:
        entity["image_url"] = image_url

    overview = wp.get("summary") or cv.get("deck")
    if overview:
        entity["overview"] = overview

    canonical_name = cv.get("real_name")
    if canonical_name and canonical_name.lower() != (entity.get("name") or "").lower().replace("_", " "):
        entity["canonical_name"] = canonical_name

    return entity
