"""Chat with the local LLM via Ollama, with long-term memory.

Every turn is also logged to data/chatlogs/ so your conversations can
later be used to fine-tune your own model (see finetune/README.md).
"""

import datetime
import json

import ollama

from app.config import CHAT_MODEL, CHATLOG_DIR
from app.memory import recall, remember


def _log_turn(user_message: str, assistant_reply: str) -> None:
    try:
        path = CHATLOG_DIR / f"{datetime.date.today().isoformat()}.jsonl"
        record = {"user": user_message, "assistant": assistant_reply}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[chatlog] skipped: {exc}")

SYSTEM_PROMPT = (
    "You are a helpful local AI assistant running entirely on the user's "
    "own computer. Be concise and practical. You are good at coding."
)


def stream_chat(message: str, history: list[dict]):
    """Yield the assistant reply incrementally. `history` is a list of
    {"role", "content"} dicts as provided by gradio's chat component."""
    system = SYSTEM_PROMPT
    memories = recall(message)
    if memories:
        system += "\n\nThings you remember about the user from past chats:\n"
        system += "\n".join(f"- {m}" for m in memories)

    messages = [{"role": "system", "content": system}]
    messages += [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)
    ]
    messages.append({"role": "user", "content": message})

    reply = ""
    for part in ollama.chat(model=CHAT_MODEL, messages=messages, stream=True):
        reply += part["message"]["content"]
        yield reply

    # after the reply finishes, log it and store anything worth remembering
    _log_turn(message, reply)
    remember(message, reply)
