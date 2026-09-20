"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    if top_k <= 0:
        return []

    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    if use_reranking:
        hybrid = rerank_rrf([dense, sparse], top_k=top_k)
    else:
        hybrid = dense[:top_k]

    # Fallback phải dùng cosine score gốc của dense, không dùng RRF score.
    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback[:top_k]
        except Exception:
            # Provider fallback không khả dụng thì giữ kết quả hybrid.
            pass

    return hybrid[:top_k]


if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)
