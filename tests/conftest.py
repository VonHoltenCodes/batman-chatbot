"""Shared pytest fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure repo root is on sys.path so `import batman_config` works under pytest.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def chatbot():
    """Build one BatmanChatbot for the whole test session (init is slow)."""
    from chatbot.core.batman_chatbot import BatmanChatbot
    return BatmanChatbot()


@pytest.fixture()
def session_store(tmp_path):
    """Fresh on-disk SessionStore per test, isolated under tmp_path."""
    from chatbot.sessions import SessionStore
    return SessionStore(tmp_path / "sessions.db", ttl_seconds=3600)
