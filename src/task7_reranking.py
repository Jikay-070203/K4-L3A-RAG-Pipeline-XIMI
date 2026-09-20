"""Task 7 - deterministic Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from .contracts import validate_document


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse rankings once with reciprocal rank scores.

    Duplicate IDs contribute at most once per input ranking. The function
    returns copies and never mutates dense/BM25 results supplied by callers.
    """
    if not isinstance(ranked_lists, list):
        raise TypeError("ranked_lists must be a list")
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    if not isinstance(k, int) or isinstance(k, bool):
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")
    if top_k <= 0:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    first_seen: dict[str, int] = {}
    encounter_order = 0
    for ranked_list in ranked_lists:
        if not isinstance(ranked_list, list):
            raise TypeError("each ranking must be a list")
        seen_in_list: set[str] = set()
        for rank, item in enumerate(ranked_list, start=1):
            validate_document(item, require_chunk=True)
            item_id = item["id"]
            if item_id in seen_in_list:
                continue
            seen_in_list.add(item_id)
            if item_id not in items:
                items[item_id] = {**item, "metadata": dict(item["metadata"])}
                first_seen[item_id] = encounter_order
                encounter_order += 1
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)

    ranked_ids = sorted(scores, key=lambda item_id: (-scores[item_id], first_seen[item_id]))
    results: list[dict] = []
    for item_id in ranked_ids[:top_k]:
        result = items[item_id].copy()
        result["metadata"] = dict(items[item_id]["metadata"])
        result["score"] = scores[item_id]
        result["retrieval_method"] = "hybrid"
        results.append(result)
    return results


if __name__ == "__main__":
    print("RRF is ready; pass dense and BM25 rankings to rerank_rrf().")
