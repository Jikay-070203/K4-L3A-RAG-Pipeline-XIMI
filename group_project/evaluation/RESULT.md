# RAG evaluation results

## Run information

| Field | Value |
|---|---|
| Evaluation date | 2026-09-20 |
| Framework and version | pytest 9.1.1; custom evaluator `scripts/evaluate_rag.py` |
| Evaluator model | Chưa đo |
| Generator model | Gemini configured in `.env`; manual generation đã chạy |
| Embedding model | BAAI/bge-m3 via sentence-transformers |
| Corpus version/commit | Local IELTS corpus; 547 indexed chunks |
| Golden dataset size | 15 |
| `top_k` | 5 in UI; manual checks used 3 and 5 |
| Fallback threshold and calibration | 0.3; calibration chính thức chưa đo |

## Configurations

- **Config A — dense-only:** 15 cases, `top_k=5`.
- **Config B — hybrid + RRF:** 15 cases, `top_k=5`.

## Overall scores

| Metric | Config A | Config B | Delta B−A |
|---|---:|---:|---:|
| Faithfulness | Chưa đo | Chưa đo | Chưa đo |
| Answer relevance | Chưa đo | Chưa đo | Chưa đo |
| Context recall proxy | 0.800000 | 0.800000 | 0.000000 |
| Context precision proxy | 0.257143 | 0.242857 | -0.014286 |
| **Average of measured proxies** | 0.528571 | 0.521429 | -0.007143 |

## A/B comparison

- Cấu hình tốt hơn: Dense-only có context precision proxy cao hơn trong lần chạy này; chưa đủ để kết luận chất lượng answer.
- Evidence: cả hai đạt context recall proxy `0.800000`; dense-only precision proxy `0.257143`, hybrid precision proxy `0.242857`.
- Trade-off latency/cost: generation sample có latency `2114.636 ms`, `1759.782 ms`, `2162.253 ms`; latency đầy đủ theo config chưa đo.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | Case expected context không nằm trong top-k | Dense-only | Chưa đo | Chưa đo | 0 | Chưa đo | retrieval | Không truy hồi source mong đợi |
| 2 | Case expected context không nằm trong top-k | Hybrid + RRF | Chưa đo | Chưa đo | 0 | Chưa đo | retrieval | RRF ưu tiên thứ hạng khác |
| 3 | Case có nhiều context không liên quan | Hybrid + RRF | Chưa đo | Chưa đo | Chưa đo | thấp hơn dense-only | retrieval | Precision proxy thấp hơn |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
---:|---|---|---|---|
| 1 | Chạy evaluator LLM cho faithfulness/relevance | Hai metric này chưa đo | Có A/B evidence đầy đủ | Cấu hình evaluator rồi chạy lại |
| 2 | Kiểm tra citation với expected context | Manual query đã sinh citation | Tăng độ tin cậy citation | Đối chiếu từng citation với source |
| 3 | Calibrate score threshold bằng query in/out-domain | Threshold 0.3 chưa calibrate chính thức | Giảm fallback sai | Đo score và refusal trên tập calibration |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
|---|---|---:|---:|---|
| PageIndex fallback | Hybrid RRF | Chưa đo | Chưa đo | Chưa có response provider thật |

## Reproducibility evidence

```text
python -m src.task4_chunking_indexing
Indexed 547 chunks

python -m pytest tests/test_contracts.py -q
15 passed

python -m pytest tests/test_acceptance.py -q
5 passed

python scripts/evaluate_rag.py
dense_only: hit_rate=0.800000, context_precision_proxy=0.257143
hybrid_rrf: hit_rate=0.800000, context_precision_proxy=0.242857
```

Faithfulness và answer relevance chưa được chạy bằng evaluator LLM. Các ô `Chưa đo` không phải số liệu ước lượng; metric có hậu tố `proxy` là phép đo source matching của evaluator nội bộ, không phải điểm RAGAS chuẩn.
