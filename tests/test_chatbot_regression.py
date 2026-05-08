"""Regression tests pinning current chatbot behavior.

These tests lock in answers for high-signal queries so we catch silent
regressions when the embeddings layer + multi-source data land in later phases.

NOTE: Pre-existing quirks (e.g. gibberish queries can return unrelated
high-confidence answers) are documented as `xfail`/loose assertions rather
than fixed here — that's Phase 3 work.
"""
from __future__ import annotations

import pytest


# (query, expected_substring_in_answer_lower, min_confidence, expected_query_type)
KNOWN_ANSWER_CASES = [
    ("Tell me about the Batmobile",   "batmobile",          0.85, "vehicle_lookup"),
    ("Who is Alfred Pennyworth?",     "alfred",             0.85, "character_lookup"),
    ("What is the Batcave?",          "batcave",            0.85, "location_lookup"),
    ("What is Wayne Manor?",          "wayne manor",        0.85, "location_lookup"),
    ("Tell me about Nightwing",       "nightwing",          0.85, "character_lookup"),
    ("Who is Commissioner Gordon?",   "gordon",             0.85, "character_lookup"),
]


@pytest.mark.parametrize("query,needle,min_conf,qtype", KNOWN_ANSWER_CASES)
def test_known_answer(chatbot, query, needle, min_conf, qtype):
    r = chatbot.process_query(query)
    assert needle in r.answer.lower(), f"Expected {needle!r} in answer for {query!r}, got: {r.answer[:200]!r}"
    assert r.confidence >= min_conf, f"Confidence {r.confidence} < {min_conf} for {query!r}"
    assert r.query_type == qtype


def test_ambiguous_robin_offers_disambiguation(chatbot):
    """'Tell me about Robin' is genuinely ambiguous (Dick, Jason, Tim, Damian, ...).

    Note: 'Tell me about the Joker' used to disambiguate too, but Phase 3 semantic
    search now confidently resolves it to the canonical Joker entity — that's an
    intentional behavior change.
    """
    r = chatbot.process_query("Tell me about Robin")
    assert ("select which one" in r.answer.lower()
            or "multiple matches" in r.answer.lower()
            or len(r.source_entities) == 0)


def test_joker_resolves_via_semantic_search(chatbot):
    """Phase 3 quality bar: 'Tell me about the Joker' now lands on THE Joker."""
    r = chatbot.process_query("Tell me about the Joker")
    assert r.confidence >= 0.75
    assert "joker" in r.answer.lower()
    # Either resolves directly or via semantic match
    assert len(r.source_entities) == 1


def test_response_dataclass_shape(chatbot):
    r = chatbot.process_query("Who is Batman?")
    # Required attributes — guards against accidental schema breakage
    assert hasattr(r, "answer")
    assert hasattr(r, "confidence")
    assert hasattr(r, "source_entities")
    assert hasattr(r, "query_type")
    assert isinstance(r.answer, str) and r.answer
    assert 0.0 <= r.confidence <= 1.0
    assert isinstance(r.source_entities, list)


def test_empty_query_does_not_crash(chatbot):
    """An empty query should return *something*, not raise."""
    r = chatbot.process_query("")
    assert isinstance(r.answer, str)
