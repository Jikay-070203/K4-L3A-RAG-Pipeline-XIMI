"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
ROOT_DIR = Path(__file__).resolve().parent.parent
STANDARDIZED_DIR = ROOT_DIR / "data" / "standardized"
LEGAL_DIR = ROOT_DIR / "data" / "landing" / "legal"
CACHE_PATH = ROOT_DIR / "pageindex_doc_ids.json"


def upload_documents() -> dict[str, str]:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY.strip():
        raise RuntimeError("PAGEINDEX_API_KEY is not configured")

    try:
        from pageindex import PageIndexClient
    except ImportError as error:
        raise RuntimeError("pageindex package is required") from error

    pdfs = sorted(LEGAL_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF documents found in {LEGAL_DIR}")

    cached: dict[str, str] = {}
    if CACHE_PATH.exists():
        try:
            loaded = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cached = {
                    str(path): str(doc_id)
                    for path, doc_id in loaded.items()
                    if str(path).strip() and str(doc_id).strip()
                }
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Invalid PageIndex cache: {CACHE_PATH}") from error

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY.strip())
    for pdf_path in pdfs:
        cache_key = pdf_path.name
        if cache_key in cached:
            print(f"Cached: {cache_key}")
            continue

        response = client.submit_document(file_path=str(pdf_path))
        if not isinstance(response, dict) or not isinstance(response.get("doc_id"), str):
            raise RuntimeError(
                f"PageIndex submit_document returned an unexpected response for {cache_key}"
            )
        cached[cache_key] = response["doc_id"]
        CACHE_PATH.write_text(
            json.dumps(cached, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Uploaded: {cache_key}")

    CACHE_PATH.write_text(
        json.dumps(cached, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return cached


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    if top_k <= 0 or not query.strip():
        return []
    if not PAGEINDEX_API_KEY.strip():
        return []

    try:
        from pageindex import PageIndexClient
    except ImportError:
        return []

    try:
        cache = upload_documents()
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY.strip())
    except (FileNotFoundError, RuntimeError, OSError):
        return []

    results: list[dict] = []
    seen: set[str] = set()

    for filename, doc_id in cache.items():
        try:
            ocr_response = client.get_ocr(doc_id, format="page")
            pages = ocr_response.get("result", [])
            page_text = {
                page.get("page_index"): page.get("markdown", "")
                for page in pages
                if isinstance(page, dict)
                and isinstance(page.get("page_index"), int)
                and isinstance(page.get("markdown"), str)
                and page.get("markdown", "").strip()
            }

            response = client.chat_completions(
                messages=[{"role": "user", "content": query}],
                doc_id=doc_id,
                stream=False,
                enable_citations=True,
            )
            citations = response.get("citations", [])
            if not isinstance(citations, list):
                continue

            for citation in citations:
                if not isinstance(citation, dict):
                    continue
                if citation.get("document") != filename:
                    continue
                page_index = citation.get("page")
                if not isinstance(page_index, int):
                    continue
                content = page_text.get(page_index, "").strip()
                if not content:
                    continue

                block_id = str(citation.get("block_id") or "page")
                result_id = f"pageindex/{filename}::page-{page_index}::{block_id}"
                if result_id in seen:
                    continue
                seen.add(result_id)
                results.append(
                    {
                        "id": result_id,
                        "content": content,
                        "score": 1.0 / (len(results) + 1),
                        "metadata": {
                            "source": f"legal/{filename}",
                            "title": Path(filename).stem.replace("_", " "),
                            "doc_type": "legal",
                            "url": None,
                            "chunk_index": page_index - 1,
                        },
                        "retrieval_method": "pageindex",
                    }
                )
                if len(results) >= top_k:
                    return results
        except Exception:
            # Provider có thể tạm thời lỗi hoặc tài liệu chưa sẵn sàng.
            continue

    return results


if __name__ == "__main__":
    upload_documents()
