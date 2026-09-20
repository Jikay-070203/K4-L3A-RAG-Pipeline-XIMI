"""Task 4 - chunk, embed and index the standardized corpus.

Provider imports stay lazy so contract tests can mock this module without
downloading a model or opening ChromaDB.
"""

from __future__ import annotations

import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Iterator

from .contracts import validate_document


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Keep imports working while a development environment is bootstrapped.
    pass


ROOT_DIR = Path(__file__).resolve().parent.parent
STANDARDIZED_DIR = ROOT_DIR / "data" / "standardized"
CHROMA_DIR = ROOT_DIR / "chroma_db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip().lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip() or "BAAI/bge-m3"
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
EMBEDDING_BATCH_SIZE = max(1, int(os.getenv("EMBEDDING_BATCH_SIZE", "32")))
INDEX_BATCH_SIZE = max(1, int(os.getenv("INDEX_BATCH_SIZE", "256")))

COLLECTION_NAME = "rag_documents"
_SUPPORTED_PROVIDERS = {"sentence_transformers", "openai", "gemini"}
_URL_PATTERN = re.compile(r"^\s*\*\*Source:\*\*\s*(\S+)\s*$", re.IGNORECASE | re.MULTILINE)
_TITLE_PATTERN = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def _batches(items: list[Any], size: int) -> Iterator[list[Any]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


@lru_cache(maxsize=4)
def _sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise RuntimeError(
            "sentence-transformers is required for EMBEDDING_PROVIDER=sentence_transformers"
        ) from error
    return SentenceTransformer(model_name)


def _validate_texts(texts: list[str]) -> None:
    if not isinstance(texts, list):
        raise TypeError("texts must be a list of strings")
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("each embedding input must be a non-empty string")


def _validate_vectors(vectors: Iterable[Iterable[float]], expected_count: int) -> list[list[float]]:
    normalized: list[list[float]] = []
    dimension: int | None = None
    for vector in vectors:
        try:
            values = [float(value) for value in vector]
        except (TypeError, ValueError) as error:
            raise RuntimeError("embedding provider returned a non-numeric vector") from error
        if not values or not all(math.isfinite(value) for value in values):
            raise RuntimeError("embedding provider returned an empty or non-finite vector")
        if dimension is None:
            dimension = len(values)
        elif len(values) != dimension:
            raise RuntimeError("embedding provider returned inconsistent dimensions")
        normalized.append(values)
    if len(normalized) != expected_count:
        raise RuntimeError(
            f"embedding provider returned {len(normalized)} vectors for {expected_count} texts"
        )
    return normalized


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts using the provider configured in ``.env``.

    Task 5 imports this function directly, guaranteeing that documents and
    queries use the same model and vector space.
    """
    _validate_texts(texts)
    if not texts:
        return []
    if EMBEDDING_PROVIDER not in _SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(_SUPPORTED_PROVIDERS))
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER={EMBEDDING_PROVIDER!r}; use {supported}")

    vectors: list[list[float]] = []
    if EMBEDDING_PROVIDER == "sentence_transformers":
        model = _sentence_transformer(EMBEDDING_MODEL)
        for batch in _batches(texts, EMBEDDING_BATCH_SIZE):
            encoded = model.encode(
                batch,
                batch_size=min(EMBEDDING_BATCH_SIZE, len(batch)),
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            vectors.extend(encoded.tolist() if hasattr(encoded, "tolist") else encoded)

    elif EMBEDDING_PROVIDER == "openai":
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("openai is required for EMBEDDING_PROVIDER=openai") from error
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or None)
        for batch in _batches(texts, EMBEDDING_BATCH_SIZE):
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(item.embedding for item in ordered)

    else:  # gemini
        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise RuntimeError("google-genai is required for EMBEDDING_PROVIDER=gemini") from error
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or None)
        config = types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
        for batch in _batches(texts, EMBEDDING_BATCH_SIZE):
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=config,
            )
            vectors.extend(embedding.values for embedding in response.embeddings)

    return _validate_vectors(vectors, len(texts))


def get_collection():
    """Create or open the persistent cosine-distance Chroma collection."""
    try:
        import chromadb
    except ImportError as error:
        raise RuntimeError("chromadb is required to open the vector store") from error

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    space = (getattr(collection, "metadata", None) or {}).get("hnsw:space")
    if space not in (None, "cosine"):
        raise RuntimeError(
            f"Collection {COLLECTION_NAME!r} uses {space!r}, expected cosine distance"
        )
    return collection


def _document_title(content: str, fallback: str) -> str:
    match = _TITLE_PATTERN.search(content)
    return match.group(1).strip() if match and match.group(1).strip() else fallback


def _document_url(content: str) -> str | None:
    match = _URL_PATTERN.search(content)
    if not match:
        return None
    value = match.group(1).strip()
    return value if value.startswith(("http://", "https://")) else None


def load_documents() -> list[dict]:
    """Load deterministic ``Document`` objects from standardized Markdown."""
    if not STANDARDIZED_DIR.exists():
        return []

    documents: list[dict] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        relative = path.relative_to(STANDARDIZED_DIR)
        doc_type = "legal" if "legal" in {part.lower() for part in relative.parts} else "news"
        document = {
            "id": relative.as_posix(),
            "content": content,
            "metadata": {
                "source": relative.as_posix(),
                "title": _document_title(content, path.stem),
                "doc_type": doc_type,
                "url": _document_url(content),
            },
        }
        validate_document(document)
        documents.append(document)
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Split documents recursively while preserving source identity."""
    if not isinstance(documents, list):
        raise TypeError("documents must be a list")
    if not documents:
        return []
    if CHUNK_OVERLAP < 0 or CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError("CHUNK_OVERLAP must be non-negative and smaller than CHUNK_SIZE")

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as error:
        raise RuntimeError("langchain-text-splitters is required for chunking") from error

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks: list[dict] = []
    seen_document_ids: set[str] = set()
    for document in documents:
        validate_document(document)
        document_id = document["id"]
        if document_id in seen_document_ids:
            raise ValueError(f"duplicate document id: {document_id}")
        seen_document_ids.add(document_id)

        texts = [text.strip() for text in splitter.split_text(document["content"]) if text.strip()]
        for index, text in enumerate(texts):
            chunk = {
                "id": f"{document_id}::chunk-{index}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Return new chunk dictionaries enriched with embedding vectors."""
    if not isinstance(chunks, list):
        raise TypeError("chunks must be a list")
    if not chunks:
        return []
    for chunk in chunks:
        validate_document(chunk, require_chunk=True)

    vectors = embed_texts([chunk["content"] for chunk in chunks])
    return [
        {**chunk, "metadata": dict(chunk["metadata"]), "embedding": vector}
        for chunk, vector in zip(chunks, vectors)
    ]


def _chroma_metadata(metadata: dict) -> dict:
    """Chroma metadata cannot store ``None``; encode it reversibly."""
    output = dict(metadata)
    if output.get("url") is None:
        output["url"] = ""
    return output


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Idempotently upsert embedded chunks into ChromaDB in bounded batches."""
    if not isinstance(chunks, list):
        raise TypeError("chunks must be a list")
    if not chunks:
        return

    seen_ids: set[str] = set()
    vector_dimension: int | None = None
    prepared_chunks: list[dict] = []
    for chunk in chunks:
        validate_document(chunk, require_chunk=True)
        if chunk["id"] in seen_ids:
            raise ValueError(f"duplicate chunk id: {chunk['id']}")
        seen_ids.add(chunk["id"])
        vector = chunk.get("embedding")
        if vector is None:
            raise ValueError(f"chunk {chunk['id']!r} is missing an embedding")
        checked = _validate_vectors([vector], 1)[0]
        if vector_dimension is None:
            vector_dimension = len(checked)
        elif len(checked) != vector_dimension:
            raise ValueError("all chunk embeddings must have the same dimension")
        prepared_chunks.append({**chunk, "embedding": checked})

    collection = get_collection()
    for batch in _batches(prepared_chunks, INDEX_BATCH_SIZE):
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in batch],
        )


def run_pipeline() -> None:
    """Run load -> chunk -> embed -> idempotent index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
