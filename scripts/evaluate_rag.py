"""Chạy evaluation tái lập cho hai cấu hình retrieval của RAG.

Script này không tự chấm chất lượng câu trả lời bằng heuristic. Nó chỉ tính
context recall/precision khi expected_context là source file cụ thể, đồng thời
lưu answer và sources để đánh giá faithfulness/relevance bằng evaluator thật.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import generate_with_citation


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT_PATH = ROOT / "group_project" / "evaluation" / "evaluation_raw.json"
TOP_K = 5


def load_golden() -> list[dict]:
    """Đọc và kiểm tra golden dataset tối thiểu."""
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list) or len(data) < 15:
        raise ValueError("golden dataset must contain at least 15 cases")
    required = {"question", "expected_answer", "expected_context"}
    for index, item in enumerate(data):
        if not required.issubset(item):
            raise ValueError(f"golden case {index} is missing required fields")
    return data


def source_matches(expected_context: str, sources: list[dict]) -> bool:
    """Kiểm tra expected_context có xuất hiện trong source IDs hay không."""
    if expected_context == "out_of_domain":
        return not sources
    return any(
        expected_context == item.get("metadata", {}).get("source")
        for item in sources
    )


def evaluate_retrieval(cases: list[dict], use_reranking: bool) -> dict:
    """Chạy retrieval và lưu kết quả từng case."""
    rows = []
    matched = 0
    total_retrieval_contexts = 0
    relevant_retrieval_contexts = 0

    for index, case in enumerate(cases, 1):
        started = time.perf_counter()
        results = retrieve(
            case["question"],
            top_k=TOP_K,
            use_reranking=use_reranking,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        sources = [item["metadata"].get("source") for item in results]
        expected = case["expected_context"]
        hit = source_matches(expected, results)
        if hit:
            matched += 1
        if expected != "out_of_domain":
            total_retrieval_contexts += len(results)
            relevant_retrieval_contexts += sum(
                1 for source in sources if source == expected
            )
        rows.append(
            {
                "index": index,
                "question": case["question"],
                "expected_context": expected,
                "retrieved_sources": sources,
                "context_hit": hit,
                "latency_ms": elapsed_ms,
            }
        )

    case_count = len(cases)
    return {
        "config": "hybrid_rrf" if use_reranking else "dense_only",
        "top_k": TOP_K,
        "case_count": case_count,
        "expected_context_hit_rate": matched / case_count,
        "context_recall_proxy": matched / case_count,
        "context_precision_proxy": (
            relevant_retrieval_contexts / total_retrieval_contexts
            if total_retrieval_contexts
            else 0.0
        ),
        "rows": rows,
    }


def collect_generation_sample(cases: list[dict]) -> dict:
    """Chạy một số generation case để lưu bằng chứng provider/citation."""
    samples = []
    for case in cases[:3]:
        started = time.perf_counter()
        result = generate_with_citation(case["question"], top_k=TOP_K)
        samples.append(
            {
                "question": case["question"],
                "answer": result["answer"],
                "retrieval_source": result["retrieval_source"],
                "source_ids": [
                    item["id"] for item in result["sources"]
                ],
                "latency_ms": (time.perf_counter() - started) * 1000,
            }
        )
    return {"sample_count": len(samples), "samples": samples}


def main() -> None:
    cases = load_golden()
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "embedding_and_generation_metrics": {
            "faithfulness": "not_measured",
            "answer_relevance": "not_measured",
        },
        "configs": [
            evaluate_retrieval(cases, use_reranking=False),
            evaluate_retrieval(cases, use_reranking=True),
        ],
        "generation": collect_generation_sample(cases),
    }
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved raw evaluation: {OUTPUT_PATH}")
    for config in output["configs"]:
        print(
            f"{config['config']}: "
            f"hit_rate={config['expected_context_hit_rate']:.6f}, "
            f"context_precision_proxy={config['context_precision_proxy']:.6f}"
        )
    print("faithfulness: not_measured")
    print("answer_relevance: not_measured")


if __name__ == "__main__":
    main()
