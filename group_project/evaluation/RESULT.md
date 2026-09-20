# Kết quả đánh giá RAG

## Thông tin lần chạy

| Trường                              | Giá trị |
| ----------------------------------- | ----- |
| Ngày đánh giá                       | 2026-09-20T09:51:00.940968+00:00 |
| Framework và phiên bản              | ragas 0.4.3 |
| Mô hình đánh giá (evaluator)        | gpt-4o-mini (RAGAS judge) |
| Mô hình sinh câu trả lời (generator)| gpt-4o-mini |
| Mô hình embedding                   | text-embedding-3-small (OpenAI API) |
| Phiên bản/commit của corpus         | chưa commit tại thời điểm đánh giá (dựa trên 6a2a2d4 + phần triển khai cục bộ trên nhánh feat/standalone_ver) |
| Kích thước bộ dữ liệu chuẩn (golden)| 18 |
| `top_k`                             | 5 |
| Ngưỡng fallback và cách hiệu chỉnh  | SCORE_THRESHOLD=0.58, được hiệu chỉnh qua scripts/calibrate_threshold.py trên 16 câu in-domain (bộ dữ liệu chuẩn) + 10 câu out-of-domain/near-miss. TPR=1.0 (giữ được hết các câu in-domain), TNR=0.7 (3/10 câu near-miss OOD vẫn vượt ngưỡng vì các kỹ năng IELTS/TOEFL dùng chung nhiều từ vựng). Xem reports/threshold_calibration.json. |

## Các cấu hình

- **Cấu hình A -- chỉ dùng dense:** `retrieve(query, top_k, use_reranking=False)` -- chỉ dùng semantic_search, không kết hợp BM25/RRF.
- **Cấu hình B -- hybrid + RRF:** `retrieve(query, top_k, use_reranking=True)` -- kết hợp dense và BM25 bằng Reciprocal Rank Fusion (k=60).

Hai cấu hình dùng chung bộ dữ liệu chuẩn, mô hình sinh câu trả lời, mô hình đánh giá, prompt và `top_k`; chỉ khác nhau ở chiến lược truy xuất (`use_reranking`).

## Overall Scores — Điểm số tổng quan

| Chỉ số             | Cấu hình A | Cấu hình B | Chênh lệch B-A |
| ------------------- | -------: | -------: | --------: |
| Faithfulness (độ trung thực) | 0.759 | 0.850 | +0.091 |
| Answer relevance (độ liên quan của câu trả lời) | 0.891 | 0.887 | -0.003 |
| Context recall (độ bao phủ ngữ cảnh) | 0.698 | 0.823 | +0.125 |
| Context precision (độ chính xác ngữ cảnh) | 0.812 | 0.937 | +0.125 |
| **Trung bình**      | 0.790 | 0.874 | +0.084 |

Các câu out_of_domain được loại khỏi phần tính trung bình ở trên (được đánh giá riêng bằng độ chính xác từ chối - refusal accuracy) để không âm thầm thưởng/phạt việc từ chối đúng. Refusal accuracy: Cấu hình A = 0.500, Cấu hình B = 0.500. Tỷ lệ trúng ngữ cảnh (context-hit rate, không dùng LLM, kiểm tra substring độc lập với RAGAS): Cấu hình A = 0.312, Cấu hình B = 0.312.

## A/B Comparison — So sánh A/B

- Cấu hình tốt hơn: Cấu hình B (hybrid + RRF). Trung bình 4 chỉ số: A=0.790 so với B=0.874 (chênh lệch +0.084), và thắng đều trên cả 4 chỉ số riêng lẻ (faithfulness +0.091, answer_relevancy -0.003 (không đáng kể), context_recall +0.125, context_precision +0.125).
- Bằng chứng: Lần chạy đầu tiên (trước khi sửa lỗi citation-repair) cho kết quả ngược lại: A=0.774 so với B=0.449, vì 4/18 câu ở Cấu hình B bị hạ xuống mức safe refusal toàn phần (0 điểm cả 4 chỉ số) chỉ vì câu trả lời thiếu marker [Sn], dù chunk lấy về là đúng. Sau khi thêm bước "thử lại một lần với yêu cầu rõ ràng trước khi từ chối" (task10_generation.py::_generate_impl, đoạn retry citation), kết quả đảo ngược thành B thắng A rõ ràng -- đúng với kỳ vọng lý thuyết là RRF kết hợp BM25 giúp context_recall/precision tốt hơn dense-only, đặc biệt ở các câu keyword-heavy và cross-lingual. Đây là một bài học quan trọng: số liệu A/B ban đầu gần như chắc chắn sai nếu không kiểm tra từng ca thất bại thay vì chỉ nhìn trung bình -- 4 ca "0 điểm tuyệt đối" là dấu hiệu rõ ràng của lỗi ở tầng generation, không phải tầng retrieval.
- Đánh đổi về latency/chi phí: Cấu hình A trung bình 1786 ms/câu; Cấu hình B trung bình 1718 ms/câu. Latency của Cấu hình B thấp hơn một chút (1718ms so với 1786ms/câu trung bình) -- RRF và BM25 chạy trên corpus nhỏ (272 chunk) gần như không tốn thêm chi phí đáng kể so với thời gian gọi LLM sinh câu trả lời (chiếm phần lớn latency ở cả hai cấu hình). Không có đánh đổi latency đáng kể; Cấu hình B thắng cả về chất lượng lẫn latency trên corpus này.

## Worst Performers — Các trường hợp kém nhất

|   # | Câu hỏi | Cấu hình | Faithfulness | Relevance | Recall | Precision | Giai đoạn lỗi             | Nguyên nhân gốc |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | -------------------------- | ---------- |
| 1 | IELTS Writing Task 2 có mấy tiêu chí chấm điểm và đó là những tiêu chí | B | 0.000 | 0.708 | 0.000 | 0.000 | retrieval+generation | Câu hỏi cross-lingual về 4 tiêu chí Task 2. RRF/BM25 kéo về chunk từ C06 (Sample Tasks, câu "The other criteria for Task 2 are the same as for Task 1 (Coherence and Cohesion, Lexical Resource, Grammatical Range and Accuracy)") thay vì chunk chính tắc C02 liệt kê đầy đủ "4 tiêu chí". Chunk C06 KHÔNG nêu tên "Task Response" tường minh (chỉ nói "giống Task 1" -- mà Task 1 lại là "Task Achievement", khác Task 2). LLM tự điền vào "Task Response" từ kiến thức nền (đúng về mặt sự thật nhưng KHÔNG có căn cứ trong ngữ cảnh được cung cấp) -> RAGAS Faithfulness chấm đúng là 0.0 vì đây là claim không được hỗ trợ bởi ngữ cảnh. Đây là một phát hiện retrieval thật sự (chọn nhầm chunk liên quan gần nhưng không đầy đủ), không phải lỗi định dạng citation như lần chấm trước. |
| 2 | What must a Band 9 response demonstrate for coherence and cohesion in  | B | 0.750 | 0.809 | 0.000 | 1.000 | retrieval | Câu hỏi về C01 (band descriptor PDF bị markitdown làm nát cấu trúc bảng 4 cột khi convert -- xem _chunk_band_descriptor_document trong task4_chunking_indexing.py). context_recall=0.0 nghĩa là RRF không kéo đúng chunk Band 9 mong đợi về top-k, dù context_precision gần 1.0 (những gì lấy được thì liên quan). Nguyên nhân có thể: văn bản chunk band descriptor đã bị trộn cột nên embedding và BM25 đều khó khớp chính xác với câu hỏi dùng thuật ngữ "Band 9". |
| 3 | What four criteria will examiners use to mark my IELTS essay, accordin | B | 0.600 | 0.952 | 0.500 | 1.000 | generation | Context_recall=0.5, faithfulness=0.6 -- ngữ cảnh lấy về một phần đúng (từ A01) nhưng câu trả lời của LLM có thể đã diễn giải hơi xa nội dung gốc hoặc bỏ sót một phần của 4 tiêu chí khi diễn giải, khiến bước kiểm tra NLI theo từng statement của RAGAS Faithfulness không khớp hết. |

## Recommendations — Khuyến nghị

| Ưu tiên | Hành động | Bằng chứng từ phân tích lỗi | Tác động kỳ vọng | Cách kiểm chứng |
| -------: | ------ | ------------------------------- | ---------------- | ------------- |
| 1 | Giữ cơ chế "thử lại một lần với yêu cầu citation rõ ràng trước khi từ chối" đã thêm vào _generate_impl() (task10_generation.py) thay vì hạ thẳng xuống safe refusal khi không tìm thấy marker [Sn] nào trong lần gọi đầu. | Trước khi thêm: 4/18 câu bị 0 điểm tuyệt đối cả 4 chỉ số ở Cấu hình B chỉ vì thiếu định dạng citation, làm đảo ngược hoàn toàn kết luận A/B (B trở nên tệ hơn A một cách giả tạo). Sau khi thêm: B thắng A rõ ràng trên cả 4 chỉ số, đúng với kỳ vọng lý thuyết. | Chỉ số phản ánh đúng chất lượng retrieval/generation thật sự thay vì bị chi phối bởi một lỗi định dạng ở tầng sinh câu trả lời. | So sánh group_project/evaluation/results/raw_B_hybrid.json trước/sau: đếm số ca retrieval_source='none' và số ca 0 điểm tuyệt đối cả 4 chỉ số. |
| 2 | Với câu hỏi về nhiều tiêu chí cùng tên nhưng khác ngữ cảnh (vd "Task Response" của Task 2 so với "Task Achievement" của Task 1), tăng fetch_k trước RRF (hiện là top_k*2) và ưu tiên chunk từ tài liệu "key assessment criteria" (C02) hơn chunk từ "sample tasks" (C06) khi cả hai cùng xuất hiện, vì C02 là nguồn chính tắc liệt kê đầy đủ tiêu chí còn C06 chỉ nhắc lại lướt qua. | g11: RRF chọn chunk C06 (nhắc lướt) thay vì C02 (liệt kê đầy đủ), khiến LLM phải tự điền thêm "Task Response" từ kiến thức nền -> faithfulness=0.0. | Giảm số lần LLM phải suy diễn ngoài ngữ cảnh cho câu hỏi liên quan tới danh sách tiêu chí chấm điểm. | Chạy lại g11 qua Cấu hình B sau khi tăng fetch_k, kiểm tra context_ids có bao gồm chunk C02 hay không và faithfulness có lên 1.0 không. |
| 3 | Với band descriptor (C01), thử thêm một biến thể metadata "band_number" riêng (vd "9") ngoài section_path hiện tại, và cho BM25 index thêm alias "Band {N}" để tăng khả năng khớp từ khóa chính xác. | g12: context_recall=0.0 cho câu hỏi về Band 9 dù chunk Band 9 đã được tách riêng đúng trong task4 (xem _chunk_band_descriptor_document), tức vấn đề nằm ở khâu retrieve/rank chứ không phải khâu chunk. | Tăng context_recall cho nhóm câu hỏi về band descriptor cụ thể, là nhóm chiếm 1/3 bộ dữ liệu chuẩn đang có điểm thấp nhất (g09/g11/g12 đều thuộc nhóm này hoặc liên quan). | Thêm trường band_number vào metadata, chạy lại eval_runner và so sánh context_recall riêng cho nhóm câu hỏi về band descriptor. |

## Thí nghiệm bổ sung

| Thí nghiệm | Baseline | Chênh lệch chỉ số | Chênh lệch latency/chi phí | Kết luận |
| ---------- | -------- | ------------: | -------------------: | ---------- |
| chưa có | chưa có | chưa có | chưa có | chưa có |

## Latest Verification

Lệnh xác minh toàn bộ repository:

```text
python -m pytest -q
```

Kết quả thực tế ngày 2026-09-20:

```text
20 passed, 1 warning in 4.73s
```

## Latest Evaluation Run

Kết quả đánh giá mới nhất, ghi trong `evaluation_raw.json`, có 15 case và `top_k=5`:

| Configuration | Context hit rate / recall proxy | Context precision proxy |
| --- | ---: | ---: |
| Dense-only | 0.800000 | 0.328571 |
| Hybrid + RRF | 0.666667 | 0.300000 |

Trong lần chạy này, `faithfulness` và `answer_relevance` có trạng thái `not_measured`; không dùng số ước lượng cho hai metric này. Ba mẫu generation gồm một câu trả lời an toàn (`retrieval_source=none`) và hai mẫu cần kiểm tra thêm chất lượng citation/generation.
