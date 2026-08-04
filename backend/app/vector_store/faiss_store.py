"""Per-user FAISS index persistence and retrieval."""

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
INDEX_ROOT = PROJECT_ROOT / "data" / "faiss_indexes"


def _user_index_dir(user_id: int) -> Path:
    """Return the folder that stores one user's FAISS files."""

    return INDEX_ROOT / f"user_{user_id}"


def _index_path(user_id: int) -> Path:
    return _user_index_dir(user_id) / "index.faiss"


def _metadata_path(user_id: int) -> Path:
    return _user_index_dir(user_id) / "metadata.json"


def _load_metadata(user_id: int) -> list[dict[str, Any]]:
    """Load stored chunk metadata for one user."""

    path = _metadata_path(user_id)
    if not path.exists():
        return []

    return json.loads(path.read_text(encoding="utf-8"))


def _save_metadata(user_id: int, metadata: list[dict[str, Any]]) -> None:
    """Save chunk metadata beside the FAISS index."""

    path = _metadata_path(user_id)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _load_or_create_index(user_id: int, dimension: int) -> faiss.Index:
    """Load an existing FAISS index or create a new cosine-similarity index."""

    path = _index_path(user_id)
    if path.exists():
        return faiss.read_index(str(path))

    # Because embeddings are normalized, inner product behaves like cosine similarity.
    return faiss.IndexFlatIP(dimension)


def add_chunks_to_user_index(
    user_id: int,
    embeddings: np.ndarray,
    chunks: list[dict[str, Any]],
    document_id: int,
    filename: str,
) -> int:
    """Append embedded chunks to one user's persisted FAISS index."""

    if len(chunks) == 0:
        return 0

    user_dir = _user_index_dir(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    index = _load_or_create_index(user_id=user_id, dimension=embeddings.shape[1])
    metadata = _load_metadata(user_id)

    start_vector_id = len(metadata)

    enriched_metadata = []
    for offset, chunk in enumerate(chunks):
        enriched_metadata.append(
            {
                "vector_id": start_vector_id + offset,
                "document_id": document_id,
                "filename": filename,
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "extraction_method": chunk["extraction_method"],
            }
        )

    index.add(embeddings)
    metadata.extend(enriched_metadata)

    faiss.write_index(index, str(_index_path(user_id)))
    _save_metadata(user_id, metadata)

    return len(enriched_metadata)


def search_user_index(
    user_id: int,
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Return the most similar chunks from one user's FAISS index."""

    index_path = _index_path(user_id)
    if not index_path.exists():
        return []

    index = faiss.read_index(str(index_path))
    metadata = _load_metadata(user_id)

    query_vector = np.asarray(query_embedding, dtype="float32")
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)

    scores, vector_ids = index.search(query_vector, top_k)

    results: list[dict[str, Any]] = []
    for score, vector_id in zip(scores[0], vector_ids[0], strict=False):
        if vector_id == -1 or vector_id >= len(metadata):
            continue

        item = dict(metadata[vector_id])
        item["score"] = float(score)
        results.append(item)

    return results
