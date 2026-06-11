"""Self-built skill library: when the agent solves a task with code, it
saves the reusable part as a named function in data/skills/ and imports
it next time instead of rewriting it. Artifact-level self-improvement —
every skill is a plain, editable Python file you can review or delete.
"""

import re

import chromadb
import ollama

from app.config import EMBED_MODEL, SKILLS_DIR, VECTOR_DB_DIR
from app.modelstate import current_model

_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
COLLECTION_NAME = "skills"

# below this embedding distance a new skill is considered already known
DUPLICATE_DISTANCE = 0.12

EXTRACT_PROMPT = (
    "You maintain a library of reusable Python skills for an AI agent. "
    "Below is a task and the code that solved it. Decide whether the "
    "code contains logic worth keeping for similar future tasks.\n\n"
    "If yes, reply in exactly this format:\n"
    "NAME: snake_case_function_name\n"
    "DESCRIPTION: one line saying what it does and when to use it\n"
    "CODE:\n```python\n<the code>\n```\n\n"
    "Rules for CODE: define exactly one top-level function whose name "
    "matches NAME; self-contained with its imports at the top; "
    "parameters instead of hardcoded file paths or values; return "
    "results instead of only printing.\n\n"
    "If the code is one-off, trivial, or too task-specific, reply with "
    "only: NONE\n\n"
    "Task: {task}\n\nCode that solved it:\n{code}"
)


def _collection():
    return _client.get_or_create_collection(COLLECTION_NAME)


def _embed(text: str) -> list[float]:
    return ollama.embed(model=EMBED_MODEL, input=[text])["embeddings"][0]


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def recall_skills(task: str, k: int = 3) -> list[str]:
    """Import hints for saved skills relevant to a task."""
    collection = _collection()
    if collection.count() == 0:
        return []
    result = collection.query(
        query_embeddings=[_embed(task)], n_results=min(k, collection.count())
    )
    return [
        f"from skills.{name} import {name}  # {description}"
        for name, description in zip(result["ids"][0], result["documents"][0])
        if (SKILLS_DIR / f"{name}.py").exists()  # user may have deleted it
    ]


def maybe_learn(task: str, code_snippets: list[str]) -> None:
    """After a task solved with code, possibly save a reusable skill.
    Never raises — learning failures must not break the chat."""
    if not code_snippets:
        return
    try:
        response = ollama.chat(
            model=current_model(),
            messages=[
                {
                    "role": "user",
                    "content": EXTRACT_PROMPT.format(
                        task=task[:1000],
                        code="\n\n".join(code_snippets)[:4000],
                    ),
                }
            ],
        )
        text = _strip_thinking(response["message"]["content"])
        if text.upper().startswith("NONE"):
            return
        name_match = re.search(r"NAME:\s*([a-zA-Z_][a-zA-Z0-9_]*)", text)
        desc_match = re.search(r"DESCRIPTION:\s*(.+)", text)
        code_match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
        if not (name_match and desc_match and code_match):
            return
        name = name_match.group(1)
        description = desc_match.group(1).strip()[:300]
        code = code_match.group(1).strip()
        if f"def {name}" not in code:
            return
        compile(code, name, "exec")  # reject broken code outright

        collection = _collection()
        embedding = _embed(f"{name}: {description}")
        if collection.count() > 0:
            nearest = collection.query(query_embeddings=[embedding], n_results=1)
            if nearest["distances"][0][0] < DUPLICATE_DISTANCE:
                return  # effectively already known
        (SKILLS_DIR / f"{name}.py").write_text(
            f'"""{description}"""\n\n{code}\n', encoding="utf-8"
        )
        collection.upsert(
            ids=[name], documents=[description], embeddings=[embedding]
        )
        print(f"[skills] learned: {name}")
    except Exception as exc:
        print(f"[skills] skipped: {exc}")


def list_skills() -> list[tuple[str, str]]:
    """All saved skills as (name, description)."""
    rows = []
    for path in sorted(SKILLS_DIR.glob("*.py")):
        try:
            first_line = path.read_text(encoding="utf-8").strip().splitlines()[0]
            description = first_line.strip('"\' ')
        except (OSError, IndexError):
            description = ""
        rows.append((path.stem, description))
    return rows
