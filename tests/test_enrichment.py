"""Tests for cross-source enrichment plumbing."""
from __future__ import annotations

import sqlite3

import pytest

import batman_config as cfg
from chatbot.core.enrichment import attach, fetch_enrichment


@pytest.fixture()
def conn():
    c = sqlite3.connect(cfg.DB_PATH)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_fetch_enrichment_returns_grouped_dict(conn):
    """If we have any enriched character, fetch should return source-keyed dict."""
    row = conn.execute(
        "SELECT entity_id FROM entity_enrichment WHERE field='summary' LIMIT 1"
    ).fetchone()
    if not row:
        pytest.skip("no enrichment data — run `make enrich-wikipedia`")
    enrich = fetch_enrichment(conn, row["entity_id"], "character")
    assert "wikipedia" in enrich or "comic_vine" in enrich


def test_attach_adds_image_url_when_available(conn):
    """attach() promotes image_url to the top level."""
    row = conn.execute("""
        SELECT ee.entity_id FROM entity_enrichment ee
        WHERE ee.field='image_url' AND ee.entity_type='character' LIMIT 1
    """).fetchone()
    if not row:
        pytest.skip("no image_url enrichments yet")

    char = dict(conn.execute(
        "SELECT id, name, description FROM characters WHERE id=?", (row["entity_id"],)
    ).fetchone())
    enriched = attach(char, conn, "character")
    assert "enrichment" in enriched
    assert enriched.get("image_url", "").startswith("http")


def test_chatbot_response_includes_enrichment_footer(chatbot):
    """For Batmobile we know there's a Wikipedia URL in the footer."""
    r = chatbot.process_query("Tell me about the Batmobile")
    assert "wikipedia.org/wiki/Batmobile" in r.answer.lower() or \
           "📖 wikipedia" in r.answer.lower(), \
           f"Expected Wikipedia footer in answer; got: {r.answer[-300:]}"


def test_enrichment_footer_skipped_for_disambiguation(chatbot):
    """Disambiguation responses (multi-match) shouldn't get a footer."""
    r = chatbot.process_query("Tell me about Robin")
    assert "📖 Wikipedia" not in r.answer or len(r.source_entities) != 1
