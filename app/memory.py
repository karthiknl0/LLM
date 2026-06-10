"""Long-term memory: the assistant remembers facts about you across
sessions. After each chat turn it extracts anything worth keeping and
stores it locally; relevant memories are recalled into every new chat.
"""

import datetime
import re
import uuid

import chromadb
import ollama

from app.config import CHAT_MODEL, EMBED_MODEL, VECTOR_DB_DIR

_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
COLLECTION_NAME = "memories"

# below this embedding distance a new fact is considered a duplicate
DUPLICATE_DISTANCE = 0.15

EXTRACT_PROMPT = (
    "You maintain long-term memory for a personal AI assistant. From the "
    "conversation turn below, extract at most ONE short fact worth "
    "remembering about the user for future conversations: preferences, "
    "projects, goals, personal details, decisions. Reply with ONLY the "
    "fact as a single sentence, or the word NONE if nothing is worth "
    "remembering.\n\nUser: {user}\n\nAssistant: {assistant}"
)


def _collection():
    return _client.get_or_create_collection(COLLECTION_NAME)


def _embed(text: str) -> list[float]:
    return ollama.embed(model=EMBED_MODEL, input=[text])["embeddings"][0]


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def recall(query: str, k: int = 5) -> list[str]:
    """Return up to k stored memories relevant to the query."""
    collection = _collection()
    if collection.count() == 0:
        return []
    result = collection.query(
        query_embeddings=[_embed(query)], n_results=min(k, collection.count())
    )
    return result["documents"][0]


def remember(user_message: str, assistant_reply: str) -> None:
    """Extract and store a memorable fact from one chat turn, if any.
    Never raises — memory failures must not break the chat."""
    try:
        response = ollama.chat(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACT_PROMPT.format(
                        user=user_message[:2000],
                        assistant=assistant_reply[:2000],
                    ),
                }
            ],
        )
        fact = _strip_thinking(response["message"]["content"])
        if not fact or fact.upper().startswith("NONE") or len(fact) > 300:
            return

        collection = _collection()
        embedding = _embed(fact)
        if collection.count() > 0:
            nearest = collection.query(query_embeddings=[embedding], n_results=1)
            if nearest["distances"][0][0] < DUPLICATE_DISTANCE:
                return  # already known

        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[fact],
            embeddings=[embedding],
            metadatas=[{"date": datetime.date.today().isoformat()}],
        )
    except Exception as exc:
        print(f"[memory] skipped: {exc}")


def list_memories() -> list[tuple[str, str]]:
    """All stored memories as (date, fact), newest first."""
    collection = _collection()
    if collection.count() == 0:
        return []
    data = collection.get()
    rows = [
        (meta.get("date", "?"), doc)
        for meta, doc in zip(data["metadatas"], data["documents"])
    ]
    return sorted(rows, reverse=True)


def clear_memories() -> str:
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return "All memories cleared."
