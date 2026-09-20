# Individual contribution report

## Thông tin

- Họ và tên: Hồ Đăng Phúc
- Mã học viên: 2A202602796
- Nhóm: XIMI
- Repository/branch: `K4-L3A-RAG-Pipeline-XIMI`, nhánh `main` (commit `5e63ac0`, `acfe29a`) và nhánh riêng `feat/standalone_ver` (commit `929ac22`), tài khoản git `AshuraOtsuki`

## Phần việc đã thực hiện

Vai trò trong nhóm: **Index & hybrid retrieval** (chunking, embedding, ChromaDB, dense search, BM25, RRF). Ngoài phần việc nhóm phân công, tôi tự triển khai thêm một bản mở rộng (standalone) trên nhánh riêng để thử nghiệm các kỹ thuật xử lý câu hỏi nâng cao.

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 4 — Chunking & indexing | Viết logic chunk theo `section_path`, xử lý riêng bảng band descriptor bị vỡ cấu trúc khi convert (`_chunk_band_descriptor_document`), build index ChromaDB idempotent | Commit `5e63ac0` (`feat: task4-7`) — `src/task4_chunking_indexing.py` (+366/-…) | Done |
| Task 5 — Dense semantic search | Chuẩn hoá hàm `semantic_search` trả về đúng schema `SearchResult`, cấu hình embedding model | Commit `5e63ac0` — `src/task5_semantic_search.py` | Done |
| Task 6 — Lexical search (BM25) | Xây BM25 index và hàm tìm kiếm lexical trả cùng schema `SearchResult` với dense search | Commit `5e63ac0` — `src/task6_lexical_search.py` | Done |
| Task 7 — Reranking/RRF | Cài Reciprocal Rank Fusion để gộp kết quả dense + BM25 một lần duy nhất theo đúng quy tắc README | Commit `5e63ac0` — `src/task7_reranking.py` | Done |
| Merge nhánh corpus vào `main` | Merge nhánh dữ liệu của thành viên 1 vào nhánh chứa task4–7 để tạo `main` thống nhất cho cả nhóm | Commit `acfe29a` (`Merge branch 'main' of .../itskathy05/K4-L3A-RAG-Pipeline-XIMI`) | Done |
| Nhánh mở rộng `feat/standalone_ver` (tự làm thêm, ngoài phân công) | Fork toàn bộ pipeline nhóm (task1–10) sang nhánh riêng và bổ sung lớp tiền xử lý truy vấn: reformulation, query expansion, query decomposition; thêm calibrate threshold, eval bằng RAGAS thật, UI inspector/trace | Commit `929ac22` (`feat: Specialized version with advance query transformation/decomposition/expanding techniques`) — `src/query_processing.py`, `src/eval_ragas.py`, `src/eval_runner.py`, `scripts/calibrate_threshold.py`, `ui/*` | Done (bản độc lập, chưa merge vào `main`) |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Bắt buộc `semantic_search` (Task 5) và BM25 search (Task 6) cùng trả về đúng một schema `SearchResult`, và chỉ chạy RRF (Task 7) đúng một lần để gộp thứ hạng thay vì gộp điểm số trực tiếp.
   **Lý do/evidence:** README quy định rõ "Dense và BM25 nên cùng trả về `SearchResult` theo một schema" và "RRF chỉ nên dùng để gộp thứ hạng và chỉ chạy một lần". Việc thống nhất schema giúp fallback (dùng cosine score gốc của dense) không bị lẫn với điểm RRF đã chuẩn hoá, tránh vi phạm pinned contract mà các test `tests/test_contracts.py` kiểm tra.
   **Trade-off:** Ràng buộc schema chung khiến BM25 search phải tính thêm một bước chuẩn hoá điểm số về cùng định dạng với dense, thêm chút overhead code so với việc để mỗi hàm tự do trả kết quả riêng.

2. **Quyết định (trên nhánh `feat/standalone_ver`):** Thêm lớp `query_processing.py` gộp 3 kỹ thuật (reformulate, expand, decompose) trong **một** LLM call duy nhất, và giữ nguyên chữ ký hàm `retrieve()` của Task 9 (không thêm tham số) — mọi sub-query đều gọi lại `retrieve()` không đổi rồi gộp kết quả theo `id` (giữ score cao nhất).
   **Lý do/evidence:** Nếu tách 3 kỹ thuật thành 3 LLM call riêng sẽ tăng latency/cost gấp 3 lần cho mỗi câu hỏi; gộp 1 call giữ pipeline nhanh. Giữ nguyên contract của `retrieve()` để không phá vỡ các test/consumer khác (chatbot, evaluation) đang dùng Task 9 nguyên bản — đây là lớp tuỳ chọn nằm ngoài rubric task1–10, không phải thay thế Task 9.
   **Trade-off:** Vì decomposition tạo nhiều sub-query rồi retrieve riêng từng cái, chi phí retrieval (không phải LLM) tăng tuyến tính theo số sub-query; đồng thời nếu LLM tiền xử lý lỗi/parse JSON thất bại, code fallback về câu hỏi gốc (identity) để không bao giờ raise lỗi ra ngoài, chấp nhận đôi khi "bỏ qua" cải thiện truy vấn thay vì cố gắng retry.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - Trên `main`: chạy `python -m src.task4_chunking_indexing` rồi `pytest -q` theo Quick start để xác nhận index build được và pass contract tests (`tests/test_contracts.py`).
  - Trên `feat/standalone_ver`: chạy `scripts/calibrate_threshold.py` trên 16 câu in-domain (golden dataset) + 10 câu out-of-domain/near-miss để hiệu chỉnh `SCORE_THRESHOLD`; chạy `src/eval_runner.py` + `eval_ragas.py` (RAGAS 0.4.3, judge `gpt-4o-mini`) trên golden dataset 18 câu, so sánh Config A (dense-only) vs Config B (hybrid + RRF).
- Kết quả trước/sau nếu có:
  - Calibrate threshold: chọn `SCORE_THRESHOLD=0.58` với TPR=1.0 (giữ hết câu in-domain) và TNR=0.7 (3/10 câu near-miss OOD vẫn vượt threshold do các kỹ năng IELTS/TOEFL dùng chung nhiều từ vựng) — chi tiết trong `reports/threshold_calibration.json`.
  - Eval A/B (nhánh standalone): trung bình 4 metric RAGAS — Config A = 0.790, Config B = 0.874 (delta +0.084); Config B thắng trên cả 4 metric riêng lẻ (faithfulness +0.091, context recall +0.125, context precision +0.125, answer relevance gần như không đổi -0.003).
  - Phát hiện đáng chú ý: lần chạy đầu tiên (trước khi sửa lỗi citation-repair trong `task10_generation.py`) cho kết quả ngược — Config B thua Config A (0.449 vs 0.774) — vì 4/18 câu ở Config B bị hạ xuống safe refusal toàn phần chỉ vì thiếu marker `[Sn]` dù chunk lấy về đúng.
- Lỗi đã phát hiện và cách xử lý: phát hiện lỗi generation-layer nêu trên bằng cách soi từng case thất bại (không chỉ nhìn trung bình); xử lý bằng cách thêm bước "thử lại một lần với yêu cầu citation rõ ràng trước khi từ chối" trong `_generate_impl()` (`src/task10_generation.py`), sau đó A/B đảo ngược đúng với kỳ vọng lý thuyết (hybrid + RRF tốt hơn dense-only).

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: ở nhánh chính, contract tests chỉ kiểm tra schema/idempotency của index chứ chưa đo chất lượng retrieval bằng metric thật (đến khi tôi làm thêm RAGAS ở nhánh riêng mới có số liệu); ngoài ra một số câu hỏi về band descriptor (Band 9) vẫn bị `context_recall=0.0` ở Config B do bảng 4 cột bị convert vỡ cấu trúc từ Task 3, ảnh hưởng tới cả embedding và BM25.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: merge các cải tiến đã kiểm chứng ở `feat/standalone_ver` (threshold calibration, RAGAS eval, retry-citation) vào `main`; đồng thời tăng `fetch_k` trước RRF và ưu tiên chunk từ tài liệu chính tắc (C02) khi có nhiều chunk liên quan cùng xuất hiện, để giảm trường hợp LLM tự suy diễn ngoài context.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Hồ Đăng Phúc
