"""Long-term memory: facts about you, plus behavioral lessons learned
when you correct the assistant. After each chat turn, both are extracted
and stored locally; relevant ones are recalled into every new chat.
"""

import datetime
import re
import uuid

import chromadb
import ollama

from app.config import EMBED_MODEL, VECTOR_DB_DIR
from app.modelstate import current_model

_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
FACTS_COLLECTION = "memories"
LESSONS_COLLECTION = "lessons"

# below this embedding distance a new entry is considered a duplicate
DUPLICATE_DISTANCE = 0.15

EXTRACT_PROMPT = (
    "You maintain long-term memory for a personal AI assistant. Analyze "
    "the conversation turn below and reply with exactly two lines:\n"
    "FACT: <one short fact worth remembering about the user — preferences, "
    "projects, goals, personal details — or NONE>\n"
    "LESSON: <ONLY if the user corrected the assistant or gave a standing "
    "instruction: one short rule for future behavior, phrased like 'When "
    "the user asks about X, do Y' — otherwise NONE>\n\n"
    "User: {user}\n\nAssistant: {assistant}"
)


def _collection(name: str):
    return _client.get_or_create_collection(name)


def _embed(text: str) -> list[float]:
    return ollama.embed(model=EMBED_MODEL, input=[text])["embeddings"][0]


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _store(collection_name: str, text: str) -> None:
    collection = _collection(collection_name)
    embedding = _embed(text)
    if collection.count() > 0:
        nearest = collection.query(query_embeddings=[embedding], n_results=1)
        if nearest["distances"][0][0] < DUPLICATE_DISTANCE:
            return  # already known
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[text],
        embeddings=[embedding],
        metadatas=[{"date": datetime.date.today().isoformat()}],
    )


def _recall_from(collection_name: str, query: str, k: int) -> list[str]:
    collection = _collection(collection_name)
    if collection.count() == 0:
        return []
    result = collection.query(
        query_embeddings=[_embed(query)], n_results=min(k, collection.count())
    )
    return result["documents"][0]


def recall(query: str, k: int = 5) -> list[str]:
    """Stored facts about the user relevant to the query."""
    return _recall_from(FACTS_COLLECTION, query, k)


def recall_lessons(query: str, k: int = 5) -> list[str]:
    """Behavioral lessons relevant to the query."""
    return _recall_from(LESSONS_COLLECTION, query, k)


def remember(user_message: str, assistant_reply: str) -> None:
    """Extract and store a fact and/or lesson from one chat turn.
    Never raises — memory failures must not break the chat."""
    try:
        response = ollama.chat(
            model=current_model(),
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
        for line in _strip_thinking(response["message"]["content"]).splitlines():
            line = line.strip()
            upper = line.upper()
            if upper.startswith("FACT:"):
                payload, target = line[5:].strip(), FACTS_COLLECTION
            elif upper.startswith("LESSON:"):
                payload, target = line[7:].strip(), LESSONS_COLLECTION
            else:
                continue
            if payload and payload.upper() != "NONE" and len(payload) <= 300:
                _store(target, payload)
    except Exception as exc:
        print(f"[memory] skipped: {exc}")


def list_memories() -> list[tuple[str, str, str]]:
    """All stored entries as (date, type, text), newest first."""
    rows = []
    for name, label in ((FACTS_COLLECTION, "fact"), (LESSONS_COLLECTION, "lesson")):
        collection = _collection(name)
        if collection.count() == 0:
            continue
        data = collection.get()
        rows += [
            (meta.get("date", "?"), label, doc)
            for meta, doc in zip(data["metadatas"], data["documents"])
        ]
    return sorted(rows, reverse=True)


def clear_memories() -> str:
    for name in (FACTS_COLLECTION, LESSONS_COLLECTION):
        try:
            _client.delete_collection(name)
        except Exception:
            pass
    return "All memories and lessons cleared."
