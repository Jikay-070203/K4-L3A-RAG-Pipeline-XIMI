"""Task 5 - dense retrieval from the shared Chroma collection."""

from __future__ import annotations

import math

from .contracts import validate_document
from .task4_chunking_indexing import embed_texts, get_collection


def _result_metadata(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    metadata = dict(value)
    if metadata.get("url") == "" or "url" not in metadata:
        metadata["url"] = None
    return metadata


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Return unique dense SearchResult objects sorted by cosine score."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    query = query.strip()
    if not query or top_k <= 0:
        return []

    collection = get_collection()
    count_method = getattr(collection, "count", None)
    collection_size = count_method() if callable(count_method) else None
    if collection_size == 0:
        return []
    n_results = min(top_k, collection_size) if isinstance(collection_size, int) else top_k

    query_vector = embed_texts([query])[0]
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    ids = (response.get("ids") or [[]])[0]
    documents = (response.get("documents") or [[]])[0]
    metadatas = (response.get("metadatas") or [[]])[0]
    distances = (response.get("distances") or [[]])[0]

    best_by_id: dict[str, dict] = {}
    for item_id, content, raw_metadata, distance in zip(ids, documents, metadatas, distances):
        metadata = _result_metadata(raw_metadata)
        if (
            not isinstance(item_id, str)
            or not item_id
            or not isinstance(content, str)
            or not content.strip()
        ):
            continue
        if metadata is None or not isinstance(distance, (int, float)) or isinstance(distance, bool):
            continue
        score = max(0.0, min(1.0, 1.0 - float(distance)))
        if not math.isfinite(score):
            continue
        result = {
            "id": item_id,
            "content": content,
            "score": score,
            "metadata": metadata,
            "retrieval_method": "dense",
        }
        try:
            validate_document(result, require_chunk=True)
        except ValueError:
            continue
        previous = best_by_id.get(item_id)
        if previous is None or score > previous["score"]:
            best_by_id[item_id] = result

    return sorted(best_by_id.values(), key=lambda item: (-item["score"], item["id"]))[:top_k]


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
