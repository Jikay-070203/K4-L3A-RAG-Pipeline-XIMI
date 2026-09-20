# Individual Contribution Report — IELTS Writing RAG

## Thông tin

- Họ và tên: Lê Nguyễn Trâm Anh
- Mã học viên: 2A202602760
- Nhóm: IELTS Writing RAG
- Repository/branch: `K4-DAY08-LeNguyenTramAnh-2A202602760`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Source registry | Xây dựng catalog nguồn IELTS Writing có ID ổn định, nhóm tài liệu, publisher, title và URL; bổ sung tài liệu C06 để corpus có đủ ba reference PDF | `ielts_writing_urls.csv` | Done |
| Task 1 — Legal/policy corpus | Xây dựng ingestion có kiểm tra HTTP, MIME/signature `%PDF`, kích thước tối thiểu, filename deterministic và cơ chế idempotent skip khi chạy lại | `src/task1_collect_legal_docs.py`, `data/landing/legal/` | Done |
| Task 2 — Article corpus | Thu thập tám trang IELTS Writing chính thức; chuẩn hóa output JSON theo schema bắt buộc; thêm retry, quality gate 200 ký tự và HTTP/BeautifulSoup fallback khi Playwright browser unavailable | `src/task2_crawl_news.py`, `data/landing/news/` | Done |
| Task 3 — Standardization | Thiết kế bước PDF-to-Markdown bằng MarkItDown và article cleaning; cắt navigation/footer, chuẩn hóa whitespace, giữ heading/nội dung chuyên môn và thêm provenance metadata | `src/task3_convert_markdown.py`, `data/standardized/` | Done |
| Data verification | Đối chiếu số lượng, metadata và độ dài nội dung; xác nhận 3 PDF, 8 JSON, 3 legal Markdown và 8 news Markdown bằng acceptance tests | `tests/test_acceptance.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Dùng registry theo ID và thiết kế ingestion idempotent.**  
   **Lý do/evidence:** `ielts_writing_urls.csv` là single source of truth; mỗi file được đặt tên từ ID như `C01_...pdf`, kiểm tra `%PDF` trước khi chấp nhận và skip nếu bản cache còn hợp lệ. Điều này bảo đảm source identity ổn định và tránh dữ liệu trùng khi chạy lại.  
   **Trade-off:** Mọi nguồn mới phải được khai báo trong CSV, đổi lại các bước crawl, convert và citation dùng chung một metadata contract.

2. **Tách raw landing data khỏi standardized corpus và làm sạch theo cấu trúc trang.**  
   **Lý do/evidence:** JSON/PDF gốc được giữ nguyên để audit; Task 3 tạo bản Markdown mới với `Document ID`, publisher, source URL, document type và crawl date. Article được cắt từ heading chính, loại boilerplate/footer và giữ lại heading, paragraph, list để chunking/retrieval có tín hiệu tốt hơn.  
   **Trade-off:** Giữ hai lớp dữ liệu làm tăng số file, nhưng bảo toàn khả năng truy nguyên nguồn và cho phép cải thiện cleaning mà không mất raw evidence.

## Kiểm thử và kết quả

- Lệnh chạy:

  ```powershell
  python -m src.task1_collect_legal_docs
  python -m src.task2_crawl_news
  python -m src.task3_convert_markdown
  pytest tests/test_acceptance.py::test_corpus_has_required_legal_documents tests/test_acceptance.py::test_corpus_has_required_news_with_metadata tests/test_acceptance.py::test_standardized_output_covers_both_source_types -q
  ```

- Kết quả: **3 acceptance tests passed**.
- Corpus đạt: **3 PDF + 8 JSON + 11 Markdown chuẩn hóa**.
- Lỗi đã xử lý: British Council PDF trả HTML thay vì PDF nên chuyển sang nguồn PDF IELTS chính thức; Playwright thiếu browser binary nên kích hoạt HTTP fallback; Markdown sau crawl được lọc navigation/footer trước khi chuẩn hóa.

## Điều còn hạn chế

- Corpus hiện được thu thập tại một thời điểm cố định; nếu nguồn chính thức cập nhật nội dung, nhóm cần chạy lại bước ingestion để đồng bộ phiên bản mới.
- Nếu có thêm thời gian, tôi sẽ bổ sung file thống kê corpus tự động (số tài liệu, số ký tự và ngày crawl) để việc theo dõi phiên bản dữ liệu thuận tiện hơn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Lê Nguyễn Trâm Anh
