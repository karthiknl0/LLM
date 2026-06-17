"""Document retrieval and question answering."""

import chromadb
import ollama

from app.core.config import (
    RERANK_CANDIDATES,
    RERANKER_MODEL,
    TOP_K,
    VECTOR_DB_DIR,
)
from app.rag.index import COLLECTION_NAME, embed
from app.session.modelstate import current_model

_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

_reranker = None


def _rerank(question: str, docs: list[str], sources: list[str]):
    """Re-score candidate chunks with a cross-encoder so only the most
    relevant reach the LLM. Falls back to embedding order if the
    reranker can't load."""
    global _reranker
    try:
        if _reranker is None:
            from sentence_transformers import CrossEncoder

            _reranker = CrossEncoder(RERANKER_MODEL)
        scores = _reranker.predict([(question, doc) for doc in docs])
        order = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
        ranked = order[:TOP_K]
        return [docs[i] for i in ranked], [sources[i] for i in ranked]
    except Exception as exc:
        print(f"[rag] reranker unavailable, using embedding order: {exc}")
        return docs[:TOP_K], sources[:TOP_K]


def retrieve_context(question: str) -> tuple[str, list[str]] | None:
    """Best document chunks for a question as (context, sources),
    or None if there is no index / nothing relevant."""
    try:
        collection = _client.get_collection(COLLECTION_NAME)
    except Exception:
        return None

    result = collection.query(
        query_embeddings=embed([question]),
        n_results=min(RERANK_CANDIDATES, collection.count()),
    )
    docs = result["documents"][0]
    sources = [m["source"] for m in result["metadatas"][0]]
    if not docs:
        return None
    docs, sources = _rerank(question, docs, sources)
    context = "\n\n---\n\n".join(
        f"[{src}]\n{doc}" for src, doc in zip(sources, docs)
    )
    return context, sources


def ask_documents(question: str) -> str:
    """Retrieve relevant chunks and answer with the local LLM."""
    retrieved = retrieve_context(question)
    if retrieved is None:
        return (
            "Nothing relevant found — is the index built? "
            "Click 'Index documents' first."
        )
    context, sources = retrieved
    response = ollama.chat(
        model=current_model(),
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer using ONLY the provided document excerpts. "
                    "Cite the source file names you used. If the answer "
                    "is not in the excerpts, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Documents:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    answer = response["message"]["content"]
    unique_sources = ", ".join(dict.fromkeys(sources))
    return f"{answer}\n\n_Sources searched: {unique_sources}_"
