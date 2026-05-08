"""Tests for the SQLite-backed SessionStore."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest


def test_get_or_create_returns_same_session_for_same_id(session_store):
    s1 = session_store.get_or_create("abc")
    s1.last_mentioned_entity = "Batman"
    session_store.save(s1)

    s2 = session_store.get_or_create("abc")
    assert s2.session_id == "abc"
    assert s2.last_mentioned_entity == "Batman"


def test_history_persists_across_loads(session_store):
    s = session_store.get_or_create("hist-test")
    s.add_to_history("who is robin?", "Robin is a teen sidekick", entity_name="Robin")
    s.add_to_history("what about him?", "...", entity_name="Robin")
    session_store.save(s)

    reloaded = session_store.get_or_create("hist-test")
    assert len(reloaded.conversation_history) == 2
    assert reloaded.last_mentioned_entity == "Robin"
    assert reloaded.conversation_history[0]["query"] == "who is robin?"


def test_numbered_options_round_trip(session_store):
    s = session_store.get_or_create("num-test")
    s.store_numbered_options(["Batman", "Joker", "Robin"], "who is the hero?")
    session_store.save(s)

    reloaded = session_store.get_or_create("num-test")
    assert reloaded.last_numbered_options == ["Batman", "Joker", "Robin"]
    assert reloaded.get_option_by_number(2) == "Joker"
    assert reloaded.get_option_by_number(99) is None


def test_pronoun_resolution_uses_last_entity(session_store):
    s = session_store.get_or_create("pronoun-test")
    s.add_to_history("tell me about the Batmobile", "...", entity_name="Batmobile")
    assert s.resolve_pronouns("what weapons does it have?") == "what weapons does Batmobile have?"
    assert s.resolve_pronouns("describe that") == "describe Batmobile"


def test_pronoun_resolution_noop_without_entity(session_store):
    s = session_store.get_or_create("noop-test")
    assert s.resolve_pronouns("what is it") == "what is it"


def test_delete_removes_session(session_store):
    s = session_store.get_or_create("del-test")
    s.last_mentioned_entity = "Joker"
    session_store.save(s)

    session_store.delete("del-test")

    fresh = session_store.get_or_create("del-test")
    assert fresh.last_mentioned_entity is None


def test_cleanup_expired_drops_old_sessions(tmp_path):
    """Manually backdate updated_at and verify cleanup_expired removes it."""
    from chatbot.sessions import SessionStore

    store = SessionStore(tmp_path / "expire.db", ttl_seconds=60)
    s = store.get_or_create("old")
    store.save(s)

    # Backdate updated_at past TTL
    import sqlite3
    with sqlite3.connect(store.db_path) as conn:
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        conn.execute("UPDATE sessions SET updated_at = ? WHERE session_id = 'old'", (old_ts,))
        conn.commit()

    removed = store.cleanup_expired()
    assert removed == 1
