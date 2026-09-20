# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Thanh Hòa
- Mã học viên: 2A202602559
- Nhóm: K4-L3A — Nhóm RAG Pipeline IELTS Writing
- Repository/branch: `K4-L3A-RAG-Pipeline-XIMI`, nhánh `main` (tài khoản git `Jikaydev`)

## Phần việc đã thực hiện

Vai trò trong nhóm: **Thành viên 3 — Pipeline, chatbot & evaluation** (fallback, generation kèm citation, Streamlit, golden dataset, báo cáo A/B).

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 9 — Retrieval pipeline & fallback | Ghép dense search, BM25, RRF (do thành viên phụ trách index dựng sẵn) thành một pipeline `retrieve()` hoàn chỉnh, áp dụng fallback theo cosine score gốc của dense retrieval | Commit `4902f11` (`update tasl 8-9-10`) — `src/task9_retrieval_pipeline.py` (+46/-…) | Done |
| Task 10 — Generation có citation | Viết logic sinh câu trả lời từ context truy hồi, chèn citation `[Sn]` theo nguồn, xử lý case an toàn khi không đủ context | Commit `4902f11` — `src/task10_generation.py` (+129/-…) | Done |
| Chatbot Streamlit / frontend | Xây `app.py` (Streamlit) hiển thị câu trả lời kèm nguồn và điểm số; đồng thời dựng thêm bản giao diện web tĩnh (`frontend/index.html`, `frontend/app.js`, `frontend/styles.css`) | Commit `4902f11` — `app.py`, `frontend/*` | Done |
| Golden dataset & evaluation script | Soạn `golden_dataset.json` (15 câu hỏi), viết `scripts/evaluate_rag.py` để tính hit-rate/context-precision proxy và chạy so sánh Config A (dense-only) vs Config B (hybrid + RRF) | Commit `4902f11` — `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/evaluation_raw.json`, `scripts/evaluate_rag.py` | Done |
| Báo cáo đánh giá nhóm | Viết `group_project/evaluation/RESULT.md` theo đúng 7 mục yêu cầu (run info, config, overall scores, A/B comparison, worst performers, recommendations, reproducibility) | Commit `4902f11` — `group_project/evaluation/RESULT.md`; docs `docs/result_8_9_10.md` | Done |
| Index để chatbot chạy được | Build và commit thư mục `chroma_db/` (index đã dựng sẵn) cùng các thư mục `data/landing`, `data/standardized` (`.gitkeep`) để repo `main` chạy được ngay không cần rebuild lại từ đầu | Commit `4902f11` — `chroma_db/*`, `data/landing/*/.gitkeep`, `data/standardized/*/.gitkeep` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng cosine score gốc của dense retrieval (không dùng điểm RRF đã fusion) làm căn cứ cho fallback trong `task9_retrieval_pipeline.py`.
   **Lý do/evidence:** README quy định rõ "Fallback dùng cosine score gốc của dense retrieval" để tránh việc điểm số sau RRF (vốn chỉ là thứ hạng chuẩn hoá, không còn ý nghĩa "độ tương đồng") bị dùng sai mục đích khi quyết định có nên từ chối trả lời hay không.
   **Trade-off:** Vì fallback không dùng chung một thang điểm với kết quả cuối cùng hiển thị cho người dùng (đã qua RRF), cần giữ lại cả hai luồng điểm số (dense score gốc và RRF score) trong pipeline, làm code Task 9 phức tạp hơn một chút so với việc dùng một điểm số duy nhất cho mọi quyết định.

2. **Quyết định:** Đo evaluation bằng bộ metric "proxy" tự viết (`scripts/evaluate_rag.py`: hit-rate, context-precision proxy dựa trên so khớp nguồn) thay vì gọi ngay một evaluator LLM đầy đủ (RAGAS) cho faithfulness/answer relevance trong lần nộp này.
   **Lý do/evidence:** Trong thời lượng làm việc được phân bổ, cần có ngay một cách đo khách quan, không phụ thuộc thêm API key/LLM judge để so sánh nhanh Config A (dense-only, hit_rate=0.800, precision_proxy=0.257) và Config B (hybrid+RRF, hit_rate=0.800, precision_proxy=0.243) và đưa vào `RESULT.md` đúng hạn; các ô "Chưa đo" (faithfulness, answer relevance) được ghi rõ minh bạch thay vì điền số liệu ước lượng.
   **Trade-off:** Proxy metric chỉ đo việc chunk trả về có đúng "nguồn mong đợi" hay không (context recall/precision proxy), không đánh giá được chất lượng nội dung câu trả lời sinh ra (faithfulness, relevance) — kết luận A/B ở mức "dense-only nhỉnh hơn về precision proxy" trong `RESULT.md` vì vậy chỉ mang tính tham khảo ban đầu, chưa đủ để kết luận cấu hình nào tạo câu trả lời tốt hơn cho người dùng.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: chạy `python -m src.task4_chunking_indexing` (547 chunks được index), `pytest tests/test_contracts.py -q` (15 passed), `pytest tests/test_acceptance.py -q` (5 passed), và `python scripts/evaluate_rag.py` để lấy số liệu A/B — toàn bộ log được ghi lại trong mục "Reproducibility evidence" của `RESULT.md`.
- Kết quả trước/sau nếu có: Config A (dense-only) — hit_rate=0.800, context_precision_proxy=0.257; Config B (hybrid+RRF) — hit_rate=0.800, context_precision_proxy=0.243 (thấp hơn A 0.014); trung bình 2 proxy: A=0.529 vs B=0.521.
- Lỗi đã phát hiện và cách xử lý: qua worst-performers, phát hiện có case mà context mong đợi không nằm trong top-k ở cả hai config (do RRF ưu tiên thứ hạng khác dense-only) và một case hybrid có nhiều context không liên quan làm giảm precision proxy; các case này được ghi cụ thể vào bảng "Worst performers" và đề xuất khắc phục (calibrate threshold, kiểm tra citation) vào bảng "Recommendations" trong `RESULT.md` thay vì chỉ báo cáo con số tổng.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: `RESULT.md` còn nhiều ô "Chưa đo" (faithfulness, answer relevance, threshold calibration chính thức) vì evaluation mới dừng ở proxy metric tự viết, chưa chạy evaluator LLM đầy đủ.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: tích hợp một evaluator LLM (ví dụ RAGAS) để đo đầy đủ 4 metric thay vì chỉ 2 proxy, và chạy calibrate threshold chính thức trên tập câu hỏi in-domain/out-of-domain thay vì dùng giá trị mặc định 0.3.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Nguyễn Thanh Hòa

## Kết quả evaluation mới nhất

Lần chạy mới nhất của `scripts/evaluate_rag.py` trên 15 case, `top_k=5`, ghi vào `group_project/evaluation/evaluation_raw.json`, cho kết quả:

| Cấu hình | Context hit rate / recall proxy | Context precision proxy |
|---|---:|---:|
| Dense-only | 0.800000 | 0.328571 |
| Hybrid + RRF | 0.666667 | 0.300000 |

`faithfulness` và `answer_relevance` chưa được đo trong script này (`not_measured`). Không dùng các số liệu cũ để đại diện cho lần chạy mới nhất.

## Xác minh mới nhất

Lệnh đã chạy tại thư mục gốc dự án:

```text
python -m pytest -q
```

Kết quả thực tế:

```text
20 passed, 1 warning in 4.73s
```

Warning duy nhất là `PytestCacheWarning` do không ghi được thư mục `.pytest_cache` vì quyền truy cập Windows; warning này không làm test thất bại. Vì vậy, bộ acceptance và contract hiện đều đạt trong lần chạy này.
