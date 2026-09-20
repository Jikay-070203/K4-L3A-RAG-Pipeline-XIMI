"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"
SOURCE_FILE = Path(__file__).parent.parent / "ielts_writing_urls.csv"
ARTICLE_IDS = ("C03", "C04", "A01", "A02", "A03", "A04", "A05", "A10")


def load_article_sources() -> list[dict[str, str]]:
    with SOURCE_FILE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id = {row["id"]: row for row in rows}
    missing = [item_id for item_id in ARTICLE_IDS if item_id not in by_id]
    if missing:
        raise ValueError(f"Missing article source IDs: {missing}")
    return [by_id[item_id] for item_id in ARTICLE_IDS]


ARTICLE_URLS = [item["url"] for item in load_article_sources()]


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "article"


def _crawl_via_requests(url: str) -> dict:
    """Small, dependency-light fallback when a local Playwright browser is absent."""
    from bs4 import BeautifulSoup

    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; IELTS-RAG-Lab/1.0)"},
        timeout=45,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for node in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
        node.decompose()
    root = soup.find("article") or soup.find("main") or soup.body
    if root is None:
        raise ValueError("Page has no readable HTML body")
    blocks = []
    for node in root.find_all(["h1", "h2", "h3", "p", "li"]):
        text = node.get_text(" ", strip=True)
        if len(text) >= 25:
            prefix = "# " if node.name == "h1" else "## " if node.name in {"h2", "h3"} else "- " if node.name == "li" else ""
            blocks.append(prefix + text)
    markdown = "\n\n".join(dict.fromkeys(blocks)).strip()
    if len(markdown) < 200:
        raise ValueError("HTTP fallback extracted too little article content")
    title = (soup.title.get_text(" ", strip=True) if soup.title else "IELTS Writing article")
    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": markdown,
    }


async def crawl_article(url: str) -> dict:
    """Crawl one public page, retrying once for transient browser failures."""
    from crawl4ai import AsyncWebCrawler

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            async with AsyncWebCrawler() as crawler:
                result = await asyncio.wait_for(crawler.arun(url=url), timeout=90)
            success = getattr(result, "success", True)
            markdown = getattr(result, "markdown", "") or ""
            if hasattr(markdown, "raw_markdown"):
                markdown = markdown.raw_markdown
            markdown = str(markdown).strip()
            if not success or len(markdown) < 200:
                raise ValueError("Crawler returned no useful Markdown")
            metadata = getattr(result, "metadata", {}) or {}
            return {
                "url": url,
                "title": str(metadata.get("title") or "IELTS Writing article").strip(),
                "date_crawled": datetime.now(timezone.utc).isoformat(),
                "content_markdown": markdown,
            }
        except Exception as error:  # provider/browser error is reported per URL
            last_error = error
            if "Executable doesn't exist" in str(error):
                break
            if attempt == 0:
                await asyncio.sleep(1)
    try:
        return await asyncio.to_thread(_crawl_via_requests, url)
    except Exception as fallback_error:
        raise RuntimeError(
            f"Unable to crawl {url}. Crawl4AI error: {last_error}; HTTP fallback: {fallback_error}"
        ) from fallback_error


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    saved = 0
    for source in load_article_sources():
        url = source["url"]
        try:
            article = await crawl_article(url)
            article["title"] = article.get("title") or source["title"]
            output = DATA_DIR / f"{source['id']}_{_slugify(source['title'])}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            saved += 1
            print(f"Saved: {output}")
        except Exception as error:
            safe_error = str(error).encode("ascii", "backslashreplace").decode("ascii")
            print(f"Failed: {url} - {safe_error}")

    valid_files = []
    for path in DATA_DIR.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            if all(str(item.get(key, "")).strip() for key in (
                "url", "title", "date_crawled", "content_markdown"
            )):
                valid_files.append(path)
        except (OSError, json.JSONDecodeError):
            continue
    if len(valid_files) < 5:
        raise RuntimeError(f"Only {len(valid_files)} valid articles are available; need at least 5")
    print(f"Ready: {len(valid_files)} valid articles ({saved} written in this run)")


if __name__ == "__main__":
    asyncio.run(crawl_all())
