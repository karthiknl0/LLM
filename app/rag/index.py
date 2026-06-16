"""Document indexing: chunk, embed, and store documents in ChromaDB."""

import chromadb
import ollama

from app.core.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENTS_DIR,
    EMBED_MODEL,
    VECTOR_DB_DIR,
)
from app.rag.readers import read_file

_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
COLLECTION_NAME = "documents"

# noise directories inside cloned repos — never worth indexing
SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__",
    ".venv", "venv", "dist", "build", ".idea", ".vscode",
}
MAX_FILE_BYTES = 1_000_000  # skip huge files (minified bundles, data dumps)


def _chunk(text: str) -> list[str]:
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for start in range(0, len(text), step):
        piece = text[start : start + CHUNK_SIZE].strip()
        if piece:
            chunks.append(piece)
    return chunks


def embed(texts: list[str]) -> list[list[float]]:
    return ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"]


def index_documents() -> str:
    """(Re)build the index from everything in data/documents/."""
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = _client.create_collection(COLLECTION_NAME)

    files = [
        p
        for p in sorted(DOCUMENTS_DIR.rglob("*"))
        if p.is_file()
        and not (set(p.parts) & SKIP_DIRS)
        and p.stat().st_size <= MAX_FILE_BYTES
    ]
    if not files:
        return f"No files found. Put PDFs, Excel files, or code into {DOCUMENTS_DIR}"

    indexed, skipped = 0, 0
    for path in files:
        text = read_file(path)
        if not text or not text.strip():
            skipped += 1
            continue
        chunks = _chunk(text)
        rel = str(path.relative_to(DOCUMENTS_DIR))
        # embed in batches to keep requests small
        for batch_start in range(0, len(chunks), 32):
            batch = chunks[batch_start : batch_start + 32]
            collection.add(
                ids=[f"{rel}::{batch_start + i}" for i in range(len(batch))],
                documents=batch,
                embeddings=embed(batch),
                metadatas=[{"source": rel}] * len(batch),
            )
        indexed += 1

    return f"Indexed {indexed} file(s) ({skipped} skipped) from {DOCUMENTS_DIR}"
