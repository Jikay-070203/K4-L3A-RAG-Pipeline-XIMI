"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os
import re

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""
SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)

    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        parts.append(
            f"[{index}] Title: {metadata['title']}\n"
            f"Source: {metadata['source']}\n"
            f"Content:\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = LLM_PROVIDER.strip().lower()
    if not LLM_MODEL.strip():
        raise RuntimeError("LLM_MODEL must be configured")

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise RuntimeError("google-genai is required for Gemini generation") from error

        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                ),
            )
        finally:
            client.close()
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Gemini returned an empty response")
        return text.strip()

    raise ValueError(f"Unsupported LLM_PROVIDER={provider!r}; currently supported: gemini")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    if not isinstance(query, str) or not query.strip():
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    if top_k <= 0:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}

    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = (
        f"Context:\n{context}\n\nQuestion: {query}\n\n"
        "Cite sources using only numeric markers such as [1] or [2]."
    )
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}

    citation_numbers = {int(value) for value in _CITATION_PATTERN.findall(answer)}
    valid_numbers = set(range(1, len(reordered) + 1))
    if not citation_numbers or not citation_numbers.issubset(valid_numbers):
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0]["retrieval_method"],
    }


if __name__ == "__main__":
    print(generate_with_citation("test query"))
