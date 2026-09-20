# Báo cáo Task 8–10

Ngày kiểm tra: 2026-09-20

## Phạm vi

- Task 8: PageIndex vectorless fallback.
- Task 9: Hybrid retrieval pipeline.
- Task 10: Generation bằng Gemini, citation và safe refusal.
- UI Streamlit: `app.py`.

## Kết quả đã kiểm chứng

### Task 9

Đã triển khai và kiểm thử:

- Gọi dense search và BM25.
- Fuse bằng RRF đúng một lần.
- Dùng dense cosine score gốc để quyết định fallback.
- Giới hạn kết quả theo `top_k`.
- Khi PageIndex lỗi, trả hybrid result thay vì làm pipeline crash.

Contract test:

```text
3 passed, 12 deselected
```

### Task 10

Đã triển khai:

- Reorder chunks không làm mutate input.
- Format context có số thứ tự, title, source và content.
- Gọi Gemini bằng `google-genai`.
- Trả safe refusal khi không có evidence, provider lỗi hoặc citation không hợp lệ.
- Kiểm tra citation dạng `[n]` có nằm trong số source đã gửi cho model.

Contract test:

```text
2 passed, 13 deselected
```

Toàn bộ contract tests:

```text
15 passed in 4.84s
```

Đã kiểm thử câu hỏi trong domain và nhận được `retrieval_source=hybrid`, answer có citation và danh sách sources.

Đã kiểm thử câu hỏi ngoài domain và nhận được:

```text
Tôi không thể xác minh thông tin này từ nguồn hiện có.
```

### UI

`app.py` đã được nối với `generate_with_citation()` và hiển thị:

- Câu trả lời.
- Retrieval source.
- Title/source/URL.
- Retrieval method.
- Score.
- Nội dung từng chunk trong expander.

Đã chạy Streamlit tại `localhost:8501` và quan sát được câu trả lời trong domain cùng safe refusal ngoài domain.

### Dữ liệu và index

Đã chạy:

```text
Indexed 547 chunks
```

Dense search và hybrid retrieval đã trả kết quả với corpus IELTS Writing thật.

## Task 8 — trạng thái trung thực

Package `pageindex==0.2.8` đã được cài và API client có các hàm `submit_document()`, `submit_query()` và `get_retrieval()`.

Tuy nhiên chưa có response retrieval thật từ tài khoản PageIndex để xác nhận cấu trúc các node/content/score. Vì nguyên tắc không đoán field response, Task 8 chưa được ghi nhận là hoàn thiện end-to-end.

Trạng thái hiện tại:

- Fallback an toàn: đã có trong Task 9.
- Provider PageIndex thật: chưa đo.
- Parse `SearchResult` từ response PageIndex: chưa xác nhận.

Khi có API key và response thật, cần kiểm tra response rồi hoàn thiện mapping:

```python
{
    "id": str,
    "content": str,
    "score": float,
    "metadata": dict,
    "retrieval_method": "pageindex"
}
```

## Acceptance tests còn thiếu

Lần chạy cuối:

```text
18 passed, 2 failed
```

Hai lỗi còn lại:

1. `group_project/evaluation/golden_dataset.json` đang rỗng.
2. `group_project/evaluation/RESULT.md` còn `TODO`.

Đây là phần evaluation, không phải lỗi contract của Task 9–10.

## Lệnh chạy lại

```powershell
python -m src.task4_chunking_indexing
python -m pytest tests/test_contracts.py -q
streamlit run app.py
python -m pytest tests/test_acceptance.py -q
python -m pytest -q
```

## Kết luận

Task 9 đã đạt contract và chạy được trên corpus thật. Task 10 đã chạy Gemini, citation, safe refusal và UI Streamlit. Task 8 mới đạt yêu cầu fallback an toàn; chưa đủ bằng chứng để tuyên bố PageIndex provider hoạt động end-to-end. Acceptance toàn bộ chưa đạt vì golden dataset và evaluation report chưa được hoàn thành.
