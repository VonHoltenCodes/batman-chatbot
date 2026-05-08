"""Tests for the embedding-based semantic search layer."""
from __future__ import annotations

import pytest

from chatbot.core.semantic_search import SemanticSearch


@pytest.fixture(scope="module")
def search():
    s = SemanticSearch.get()
    if not s.available:
        pytest.skip(f"Embeddings index not built: {s.reason}")
    return s


def test_natural_language_query_finds_batmobile(search):
    hits = search.search("flying vehicle Batman uses", top_k=5)
    assert any("Bat" in h.name and h.entity_type == "vehicle" for h in hits[:3])


def test_natural_language_query_finds_batcave(search):
    hits = search.search("place where Batman keeps his gear", top_k=5)
    assert any("Batcave" in h.name for h in hits[:3])


def test_thomas_wayne_findable_with_clear_phrasing(search):
    hits = search.search("Bruce Wayne's father", top_k=5)
    names = [h.name for h in hits[:3]]
    assert "Thomas_Wayne" in names


def test_score_ordering(search):
    hits = search.search("Bruce Wayne", top_k=5)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_chatbot_recovers_from_keyword_failure_via_semantic(chatbot):
    """End-to-end: query that the keyword pipeline fails on should now answer."""
    r = chatbot.process_query("what flying vehicle does Batman use")
    # Pre-Phase-3 this returned conf=0.0 + "I don't have information"
    assert r.confidence > 0.5
    assert "i don't have information" not in r.answer.lower()
