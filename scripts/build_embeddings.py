#!/usr/bin/env python3
"""Build the ChromaDB vector index over all entities + their enrichment.

For each entity we combine: name, aliases (when the table exists), the
existing fandom description, Wikipedia summary, and Comic Vine deck — then
embed with sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast on CPU).

The collection is keyed by `f"{entity_type}:{entity_id}"` so retrieval
results map cleanly back to existing rows.

Run via `make embed` or `python3 scripts/build_embeddings.py`.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

# CUDA 13 prebuilt kernels dropped Pascal — force CPU unless the user overrides.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import batman_config as cfg  # noqa: E402

ENTITY_TABLES = {
    "character": ("characters", "character_aliases", "character_id", "alias"),
    "vehicle": ("vehicles", "vehicle_aliases", "vehicle_id", "alias"),
    "location": ("locations", None, None, None),
    "storyline": ("storylines", None, None, None),
    "organization": ("organizations", None, None, None),
}

COLLECTION = "batman_entities"


def _aliases(conn: sqlite3.Connection, etype: str, entity_id: str) -> list[str]:
    spec = ENTITY_TABLES[etype]
    if spec[1] is None:
        return []
    table, fk, col = spec[1], spec[2], spec[3]
    rows = conn.execute(f"SELECT {col} FROM {table} WHERE {fk} = ?", (entity_id,)).fetchall()
    return [r[0] for r in rows if r[0]]


def _enrichment_blob(conn: sqlite3.Connection, etype: str, entity_id: str) -> dict:
    rows = conn.execute(
        """
        SELECT source, field, value FROM entity_enrichment
        WHERE entity_id = ? AND entity_type = ? AND field IN ('summary', 'deck', 'real_name', 'aliases')
        """,
        (entity_id, etype),
    ).fetchall()
    out: dict = {}
    for src, field, val in rows:
        if val:
            out[f"{src}.{field}"] = val
    return out


def _build_text(name: str, aliases: list[str], description: str, enrich: dict) -> str:
    """Combine all available text into a single embedding input."""
    parts = [f"Name: {name}"]
    if enrich.get("comic_vine.real_name"):
        parts.append(f"Real name: {enrich['comic_vine.real_name']}")
    if aliases:
        parts.append("Aliases: " + ", ".join(aliases[:8]))
    if enrich.get("comic_vine.aliases"):
        parts.append(f"More aliases: {enrich['comic_vine.aliases'][:300]}")
    if enrich.get("wikipedia.summary"):
        parts.append(f"Overview: {enrich['wikipedia.summary'][:1200]}")
    if enrich.get("comic_vine.deck"):
        parts.append(f"Bio: {enrich['comic_vine.deck'][:600]}")
    if description:
        parts.append(f"Details: {description[:1200]}")
    return "\n".join(parts)


def build(force_rebuild: bool = False) -> dict:
    from sentence_transformers import SentenceTransformer
    import chromadb

    cfg.ensure_dirs()
    cfg.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading embedding model: {cfg.EMBED_MODEL_NAME}")
    model = SentenceTransformer(cfg.EMBED_MODEL_NAME, device="cpu")

    print(f"Opening ChromaDB at {cfg.CHROMA_DIR}")
    client = chromadb.PersistentClient(path=str(cfg.CHROMA_DIR))

    if force_rebuild:
        try:
            client.delete_collection(COLLECTION)
            print("  cleared existing collection")
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    conn = sqlite3.connect(cfg.DB_PATH)

    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []
    name_index: dict[str, str] = {}

    print("\nReading entities + enrichment...")
    for etype, (table, *_rest) in ENTITY_TABLES.items():
        for row in conn.execute(f"SELECT id, name, description FROM {table}"):
            entity_id, name, description = row
            aliases = _aliases(conn, etype, entity_id)
            enrich = _enrichment_blob(conn, etype, entity_id)
            text = _build_text(name, aliases, description or "", enrich)

            cid = f"{etype}:{entity_id}"
            ids.append(cid)
            texts.append(text)
            metadatas.append({
                "entity_type": etype,
                "entity_id": entity_id,
                "name": name,
                "has_wikipedia": "wikipedia.summary" in enrich,
                "has_comic_vine": "comic_vine.deck" in enrich,
            })
            name_index[name] = cid

    print(f"Embedding {len(texts)} entities (CPU)...")
    t0 = time.time()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64).tolist()
    print(f"  done in {time.time() - t0:.1f}s")

    # Chroma upserts; flush in batches to be polite.
    print("Writing to ChromaDB...")
    BATCH = 500
    for i in range(0, len(ids), BATCH):
        collection.upsert(
            ids=ids[i:i + BATCH],
            embeddings=embeddings[i:i + BATCH],
            documents=texts[i:i + BATCH],
            metadatas=metadatas[i:i + BATCH],
        )

    return {
        "indexed": len(ids),
        "by_type": {
            etype: sum(1 for m in metadatas if m["entity_type"] == etype)
            for etype in ENTITY_TABLES
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true", help="Drop & recreate the collection")
    args = parser.parse_args()

    print("🦇 Building Batman embeddings index")
    stats = build(force_rebuild=args.rebuild)
    print(f"\n✅ Indexed {stats['indexed']} entities")
    for etype, count in stats["by_type"].items():
        print(f"   {etype:12} {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
