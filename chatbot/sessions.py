"""SQLite-backed conversation session store.

Replaces the in-memory `session_store = {}` dict in web_app.py so sessions
survive server restarts and can be cleaned up by TTL.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class ConversationSession:
    session_id: str
    last_numbered_options: list = field(default_factory=list)
    conversation_history: list = field(default_factory=list)
    last_mentioned_entity: Optional[str] = None
    last_query_context: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # --- behavior preserved from the old in-memory ConversationSession ---

    def store_numbered_options(self, options: list, query: str) -> None:
        self.last_numbered_options = list(options or [])
        self.conversation_history.append({
            "type": "numbered_options",
            "query": query,
            "options": list(options or []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_option_by_number(self, number: int):
        if 1 <= number <= len(self.last_numbered_options):
            return self.last_numbered_options[number - 1]
        return None

    def clear_numbered_options(self) -> None:
        self.last_numbered_options = []

    def add_to_history(self, query: str, response: str, entity_name: Optional[str] = None) -> None:
        self.conversation_history.append({
            "type": "qa_pair",
            "query": query,
            "response": response,
            "entity_name": entity_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if entity_name:
            self.last_mentioned_entity = entity_name
            self.last_query_context = query

    def get_last_mentioned_entity(self) -> Optional[str]:
        return self.last_mentioned_entity

    def resolve_pronouns(self, query: str) -> str:
        if not self.last_mentioned_entity:
            return query
        for pat in (r"\bit\b", r"\bthat\b", r"\bthis\b"):
            if re.search(pat, query, flags=re.IGNORECASE):
                return re.sub(pat, self.last_mentioned_entity, query, flags=re.IGNORECASE)
        return query


class SessionStore:
    """Thread-safe SQLite session store with TTL-based eviction."""

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        data       TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at);
    """

    def __init__(self, db_path: Path | str, ttl_seconds: int):
        self.db_path = Path(db_path)
        self.ttl = timedelta(seconds=ttl_seconds)
        self._lock = threading.Lock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(self._SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, isolation_level=None, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def get_or_create(self, session_id: str) -> ConversationSession:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row is None:
                sess = ConversationSession(session_id=session_id)
                conn.execute(
                    "INSERT INTO sessions(session_id, data, updated_at) VALUES (?, ?, ?)",
                    (session_id, json.dumps(asdict(sess)), datetime.now(timezone.utc).isoformat()),
                )
                return sess
            return _deserialize(row[0])

    def save(self, sess: ConversationSession) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET data = ?, updated_at = ? WHERE session_id = ?",
                (json.dumps(asdict(sess)), datetime.now(timezone.utc).isoformat(), sess.session_id),
            )

    def delete(self, session_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

    def cleanup_expired(self) -> int:
        cutoff = (datetime.now(timezone.utc) - self.ttl).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE updated_at < ?", (cutoff,))
            return cur.rowcount or 0


def _deserialize(blob: str) -> ConversationSession:
    raw: dict[str, Any] = json.loads(blob)
    return ConversationSession(
        session_id=raw["session_id"],
        last_numbered_options=raw.get("last_numbered_options", []),
        conversation_history=raw.get("conversation_history", []),
        last_mentioned_entity=raw.get("last_mentioned_entity"),
        last_query_context=raw.get("last_query_context"),
        created_at=raw.get("created_at", datetime.now(timezone.utc).isoformat()),
    )
