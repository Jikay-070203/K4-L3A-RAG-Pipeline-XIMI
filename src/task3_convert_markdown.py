"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import csv
import json
import re
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"
SOURCE_FILE = Path(__file__).parent.parent / "ielts_writing_urls.csv"


def _source_catalog() -> dict[str, dict[str, str]]:
    with SOURCE_FILE.open(encoding="utf-8-sig", newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def _document_id(path: Path) -> str:
    return path.stem.split("_", 1)[0]


def _header(source: dict[str, str], doc_type: str, crawled: str = "") -> str:
    return (
        f"# {source['title']}\n\n"
        f"**Document ID:** {source['id']}\n\n"
        f"**Publisher:** {source['publisher']}\n\n"
        f"**Source:** {source['url']}\n\n"
        f"**Document type:** {doc_type}\n\n"
        f"**Crawled:** {crawled or 'source document'}\n\n---\n\n"
    )


def clean_article_markdown(markdown: str) -> str:
    """Keep the article body and remove common navigation/footer boilerplate.

    Crawl output from IELTS pages contains the site-wide navigation before the
    first H1 and promotional/footer sections after the article.  This function
    intentionally uses conservative, text-only rules so assessment content,
    headings and lists remain available to retrieval.
    """
    text = markdown.replace("\r\n", "\n").replace("\r", "\n").strip()
    heading_matches = list(re.finditer(r"(?m)^#\s+.+$", text))
    if heading_matches:
        writing_heading = next(
            (match for match in heading_matches if "writing" in match.group(0).lower()),
            heading_matches[0],
        )
        text = text[writing_heading.start() :]

    footer_markers = (
        "\n### Learn about the other sections of the test",
        "\n### Prepare for your test",
        "\nNeed help finding something?",
        "\n©",
    )
    for marker in footer_markers:
        position = text.find(marker)
        if position >= 0:
            text = text[:position]

    cleaned_lines: list[str] = []
    ignored_fragments = (
        "legal & policies",
        "sitemap",
        "accessibility",
        "complaints",
        "linkedin.com",
        "youtube.com",
        "instagram.com",
        "facebook.com",
    )
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if not line or re.fullmatch(r"!?\[.*?\]\([^)]*\)", line):
            cleaned_lines.append("")
            continue
        if line.startswith("!") or any(fragment in lower for fragment in ignored_fragments):
            continue
        cleaned_lines.append(line)

    # Preserve paragraphs but collapse crawler-created blank-line noise.
    result: list[str] = []
    for line in cleaned_lines:
        if line or (result and result[-1]):
            result.append(line)
    return "\n".join(result).strip()


def convert_legal_docs() -> None:
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog = _source_catalog()
    converter = MarkItDown()
    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        item_id = _document_id(path)
        if item_id not in catalog:
            raise ValueError(f"No catalog entry for {path.name}")
        content = converter.convert(str(path)).text_content.strip()
        if len(content) < 200:
            raise ValueError(f"Converted content is too short: {path.name}")
        output = output_dir / f"{path.stem}.md"
        output.write_text(_header(catalog[item_id], "legal") + content + "\n", encoding="utf-8")
        print(f"Saved: {output}")


def convert_news_articles() -> None:
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog = _source_catalog()
    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        item_id = _document_id(path)
        if item_id not in catalog:
            raise ValueError(f"No catalog entry for {path.name}")
        content = clean_article_markdown(str(data.get("content_markdown", "")))
        if len(content) < 200:
            raise ValueError(f"Article content is too short: {path.name}")
        source = {**catalog[item_id], "title": str(data.get("title") or catalog[item_id]["title"])}
        output = output_dir / f"{path.stem}.md"
        output.write_text(
            _header(source, "news", str(data.get("date_crawled", ""))) + content + "\n",
            encoding="utf-8",
        )
        print(f"Saved: {output}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
