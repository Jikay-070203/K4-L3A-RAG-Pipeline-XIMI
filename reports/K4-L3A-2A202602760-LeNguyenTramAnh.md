# Individual Contribution Report — IELTS Writing RAG

## Thông tin

- Họ và tên: Lê Nguyễn Trâm Anh
- Mã học viên: 2A202602760
- Nhóm: K4-L3A — Nhóm RAG Pipeline IELTS Writing
- Repository/branch: `K4-L3A-RAG-Pipeline-XIMI`, nhánh `main` (tài khoản git `itskathy05`)

## Phần việc đã thực hiện

Vai trò trong nhóm: **Thành viên 1 — Data & Corpus Lead** (thiết kế nguồn dữ liệu, ingestion, quality gate và standardized corpus cho toàn bộ RAG pipeline).

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 — Thu thập reference corpus | Sưu tầm và tải 3 PDF IELTS Writing chính thức; xây dựng ingestion đọc registry theo ID, kiểm tra HTTP/status, kích thước, MIME/signature `%PDF`, filename deterministic và skip cache hợp lệ | Commit `7277ec5`; `src/task1_collect_legal_docs.py`; `data/landing/legal/` | Done |
| Task 2 — Article corpus | Thu thập 8 trang IELTS Writing chính thức; xuất JSON đúng schema metadata; bổ sung retry, quality gate và HTTP/BeautifulSoup fallback để pipeline không phụ thuộc browser binary | Commit `7277ec5`; `src/task2_crawl_news.py`; `data/landing/news/` | Done |
| Task 3 — Standardization & cleaning | Convert PDF bằng MarkItDown; chuẩn hóa article Markdown; thêm provenance header; cắt navigation/footer và loại boilerplate trước khi corpus được bàn giao cho chunking/indexing | Commits `7277ec5`, `e8c0ede`; `src/task3_convert_markdown.py`; `data/standardized/` | Done |
| Corpus handoff | Bàn giao corpus có thể tái chạy cho các task retrieval/evaluation và đưa thay đổi vào `main` | Merge commit `acfe29a` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Thiết kế corpus hai lớp `landing` → `standardized`, phân loại nguồn theo ID và loại tài liệu.
   **Lý do/evidence:** Ba PDF criteria/reference được giữ nguyên trong `data/landing/legal`, tám webpage được lưu JSON trong `data/landing/news`, sau đó tạo bản Markdown có `Document ID`, publisher, URL, document type và crawl date. Cách này bảo toàn raw evidence để audit nhưng cung cấp input sạch, đồng nhất cho chunking, embedding và citation.
   **Trade-off:** Có thêm một bước chuẩn hóa và thêm file metadata, nhưng đổi lại mọi chunk phía sau đều truy được nguồn gốc và có thể tái tạo corpus từ registry.

2. **Quyết định:** Áp dụng cleaning heuristic có cấu trúc cho article Markdown thay vì sửa nội dung theo cảm tính từng file.
   **Lý do/evidence:** `clean_article_markdown()` cắt phần trước heading chính, dừng tại footer/promotion marker, loại ảnh/social/navigation boilerplate, chuẩn hóa newline và giữ lại heading, paragraph, list. Nhờ vậy corpus sau clean phù hợp hơn cho retrieval mà vẫn giữ nguyên nội dung IELTS Writing và provenance.
   **Trade-off:** Một số formatting phức tạp của HTML được đơn giản hóa thành Markdown text; đổi lại tín hiệu nội dung chính rõ hơn và quy tắc có thể chạy lại nhất quán cho nguồn mới.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: chạy tuần tự ba command Task 1–3 theo Quick start và chạy ba acceptance test cho legal files, news metadata và standardized output.
- Kết quả: corpus đạt **3 PDF + 8 JSON + 3 legal Markdown + 8 news Markdown**; ba acceptance tests về corpus đều **passed**; mỗi standardized document vượt ngưỡng 200 ký tự và giữ metadata nguồn.
- Lỗi đã phát hiện và cách xử lý: một nguồn PDF trả HTML nên được thay bằng PDF IELTS chính thức khác; môi trường thiếu Playwright Chromium nên kích hoạt HTTP fallback; nội dung crawl thô có navigation/footer nên được làm sạch bằng heuristic trước khi bàn giao.

## Điều còn hạn chế

- Một cải tiến tiếp theo là bổ sung corpus manifest có hash, số ký tự và ngày crawl để theo dõi phiên bản dữ liệu thuận tiện hơn.
- Ưu tiên tiếp theo là thêm test regression cho cleaning heuristic khi nhóm mở rộng registry sang nguồn mới.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Lê Nguyễn Trâm Anh
