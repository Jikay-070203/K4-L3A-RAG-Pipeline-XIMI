"""Task 6 - BM25 lexical retrieval over the indexed chunk corpus."""

from __future__ import annotations

import math
import re

from .contracts import validate_document
from .task4_chunking_indexing import get_collection


CORPUS: list[dict] = []
_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.casefold())


def _restore_metadata(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    metadata = dict(value)
    if metadata.get("url") == "" or "url" not in metadata:
        metadata["url"] = None
    return metadata


def _load_indexed_corpus() -> list[dict]:
    response = get_collection().get(include=["documents", "metadatas"])
    ids = response.get("ids") or []
    documents = response.get("documents") or []
    metadatas = response.get("metadatas") or []
    corpus: list[dict] = []
    for item_id, content, raw_metadata in zip(ids, documents, metadatas):
        metadata = _restore_metadata(raw_metadata)
        item = {"id": item_id, "content": content, "metadata": metadata}
        try:
            validate_document(item, require_chunk=True)
        except ValueError:
            continue
        corpus.append(item)
    return corpus


def build_bm25_index(corpus: list[dict]):
    """Build a BM25Okapi index from valid Task 4 chunks."""
    if not isinstance(corpus, list):
        raise TypeError("corpus must be a list")
    if not corpus:
        raise ValueError("cannot build a BM25 index from an empty corpus")
    for item in corpus:
        validate_document(item, require_chunk=True)
    try:
        from rank_bm25 import BM25Okapi
    except ImportError as error:
        raise RuntimeError("rank-bm25 is required for lexical search") from error
    return BM25Okapi([_tokenize(item["content"]) for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Return exact-term BM25 matches sorted by score descending."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    query_tokens = _tokenize(query)
    if not query_tokens or top_k <= 0:
        return []

    corpus = CORPUS if CORPUS else _load_indexed_corpus()
    if not corpus:
        return []
    bm25 = build_bm25_index(corpus)
    scores = bm25.get_scores(query_tokens)
    query_token_set = set(query_tokens)

    candidates: list[tuple[int, float, int]] = []
    for index, (item, raw_score) in enumerate(zip(corpus, scores)):
        score = float(raw_score)
        overlap = len(query_token_set.intersection(_tokenize(item["content"])))
        if overlap == 0 or not math.isfinite(score):
            continue
        candidates.append((index, score, overlap))
    candidates.sort(key=lambda value: (-value[1], -value[2], value[0]))

    results: list[dict] = []
    seen_ids: set[str] = set()
    for index, score, _ in candidates:
        item = corpus[index]
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": score,
                "metadata": dict(item["metadata"]),
                "retrieval_method": "bm25",
            }
        )
        if len(results) >= top_k:
            break
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
