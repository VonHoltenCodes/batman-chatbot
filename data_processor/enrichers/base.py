"""Shared scaffolding for cross-source enrichers.

An enricher reads existing entities from the SQLite database, looks them up
in an external source, and writes the new fields back into the
`entity_enrichment` EAV table. All enrichers are idempotent: a re-run of the
same source replaces only its own rows for the same (entity, field).
"""
from __future__ import annotations

import logging
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

# Make repo root importable when scripts are run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import batman_config as cfg  # noqa: E402

log = logging.getLogger(__name__)


ENTITY_TABLES = {
    "character": "characters",
    "vehicle": "vehicles",
    "location": "locations",
    "storyline": "storylines",
    "organization": "organizations",
}


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    entity_type: str  # 'character' | 'vehicle' | ...
    description: str | None = None


def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(cfg.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def iter_entities(
    conn: sqlite3.Connection,
    types: Iterable[str] | None = None,
    limit: int | None = None,
) -> Iterator[Entity]:
    """Yield entities from the requested tables (default: all)."""
    selected = list(types) if types else list(ENTITY_TABLES)
    yielded = 0
    for etype in selected:
        table = ENTITY_TABLES[etype]
        for row in conn.execute(f"SELECT id, name, description FROM {table}"):
            yield Entity(id=row["id"], name=row["name"], entity_type=etype, description=row["description"])
            yielded += 1
            if limit is not None and yielded >= limit:
                return


def write_enrichment(
    conn: sqlite3.Connection,
    entity: Entity,
    source: str,
    fields: dict[str, str | None],
) -> None:
    """Upsert one or more fields for a single entity from a single source."""
    rows = [
        (entity.id, entity.entity_type, source, field, value)
        for field, value in fields.items()
        if value is not None
    ]
    if not rows:
        return
    conn.executemany(
        """
        INSERT INTO entity_enrichment(entity_id, entity_type, source, field, value)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(entity_id, entity_type, source, field)
        DO UPDATE SET value = excluded.value, fetched_at = CURRENT_TIMESTAMP
        """,
        rows,
    )


def already_enriched(
    conn: sqlite3.Connection,
    entity: Entity,
    source: str,
    field: str = "_status",
) -> bool:
    """True if we've already attempted this entity from this source."""
    row = conn.execute(
        """
        SELECT 1 FROM entity_enrichment
        WHERE entity_id = ? AND entity_type = ? AND source = ? AND field = ?
        """,
        (entity.id, entity.entity_type, source, field),
    ).fetchone()
    return row is not None


def mark_status(conn: sqlite3.Connection, entity: Entity, source: str, status: str) -> None:
    """Record that we've processed this entity (regardless of result)."""
    write_enrichment(conn, entity, source, {"_status": status})


class RateLimiter:
    """Simple token-spacing rate limiter (request every `min_interval_s`)."""

    def __init__(self, min_interval_s: float):
        self.min_interval = min_interval_s
        self._last = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()
