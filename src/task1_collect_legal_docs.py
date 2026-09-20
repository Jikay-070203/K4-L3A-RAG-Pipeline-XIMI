"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

import csv
import re
from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
ROOT_DIR = Path(__file__).parent.parent
SOURCE_FILE = ROOT_DIR / "ielts_writing_urls.csv"
LEGAL_IDS = {"C01", "C02", "C06"}


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value or "document"


def _is_valid_pdf(path: Path) -> bool:
    """A valid cached source is a non-trivial file with a PDF signature."""
    try:
        return path.stat().st_size > 1024 and path.read_bytes()[:4] == b"%PDF"
    except OSError:
        return False


def load_legal_sources() -> list[dict[str, str]]:
    """Read the three selected reference PDFs from the shared source catalog."""
    with SOURCE_FILE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row.get("id") in LEGAL_IDS]
    missing = LEGAL_IDS - {row["id"] for row in selected}
    if missing:
        raise ValueError(f"Missing legal source IDs in {SOURCE_FILE.name}: {sorted(missing)}")
    return sorted(selected, key=lambda item: item["id"])


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    setup_directory()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; IELTS-RAG-Lab/1.0)"}
    for source in load_legal_sources():
        filename = f"{source['id']}_{_slugify(source['title'].removesuffix(' PDF'))}.pdf"
        output = DATA_DIR / filename
        if _is_valid_pdf(output):
            print(f"Exists: {output}")
            continue

        try:
            response = requests.get(source["url"], headers=headers, timeout=60)
            response.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(f"Failed to download {source['id']} from {source['url']}: {error}") from error
        content_type = response.headers.get("content-type", "").lower()
        payload = response.content
        if "pdf" not in content_type and not payload.startswith(b"%PDF"):
            raise ValueError(f"Expected a PDF from {source['url']}, got {content_type!r}")
        if len(payload) <= 1024:
            raise ValueError(f"Downloaded PDF is unexpectedly small: {source['url']}")
        output.write_bytes(payload)
        print(f"Saved: {output}")


if __name__ == "__main__":
    download_documents()
