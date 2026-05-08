"""Lightweight wrapper around the ChromaDB collection built by
scripts/build_embeddings.py. Lazily loads model + collection so the chatbot
can boot without paying the embedding-model cost when it isn't needed.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Force CPU; CUDA 13 prebuilt wheels dropped Pascal (1080 Ti).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import batman_config as cfg  # noqa: E402

COLLECTION = "batman_entities"


@dataclass
class SemanticHit:
    entity_id: str
    entity_type: str
    name: str
    score: float  # cosine similarity in [0, 1]; higher is better
    document: str = ""


class SemanticSearch:
    """Singleton-ish wrapper. Returns [] if the index hasn't been built yet."""

    _instance: Optional["SemanticSearch"] = None

    @classmethod
    def get(cls) -> "SemanticSearch":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._model = None
        self._collection = None
        self._available = False
        self._reason: str | None = None
        self._init_collection()

    def _init_collection(self) -> None:
        if not cfg.CHROMA_DIR.exists():
            self._reason = f"{cfg.CHROMA_DIR} not found — run `make embed` to build the index."
            return
        try:
            import chromadb
        except ImportError as exc:
            self._reason = f"chromadb not installed ({exc})"
            return

        try:
            client = chromadb.PersistentClient(path=str(cfg.CHROMA_DIR))
            try:
                self._collection = client.get_collection(COLLECTION)
            except Exception:
                self._reason = "ChromaDB collection not found — run `make embed`."
                return
            if self._collection.count() == 0:
                self._reason = "ChromaDB collection empty — run `make embed`."
                return
            self._available = True
        except Exception as exc:
            self._reason = f"chromadb init failed: {exc}"

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(f"sentence-transformers not installed ({exc})")
        self._model = SentenceTransformer(cfg.EMBED_MODEL_NAME, device="cpu")

    @property
    def available(self) -> bool:
        return self._available

    @property
    def reason(self) -> str | None:
        return self._reason

    def search(
        self,
        query: str,
        top_k: int = 5,
        entity_types: list[str] | None = None,
    ) -> list[SemanticHit]:
        if not self._available or not query.strip():
            return []

        self._ensure_model()
        embedding = self._model.encode([query], show_progress_bar=False).tolist()[0]

        where = None
        if entity_types:
            where = {"entity_type": {"$in": entity_types}}

        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
        )

        hits: list[SemanticHit] = []
        ids = (result.get("ids") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]

        for cid, meta, dist, doc in zip(ids, metadatas, distances, documents):
            # Chroma cosine distance ∈ [0, 2]; convert to similarity in [0, 1].
            score = max(0.0, 1.0 - dist / 2.0)
            hits.append(SemanticHit(
                entity_id=meta.get("entity_id", cid.split(":", 1)[-1]),
                entity_type=meta.get("entity_type", "unknown"),
                name=meta.get("name", ""),
                score=score,
                document=doc or "",
            ))
        return hits
