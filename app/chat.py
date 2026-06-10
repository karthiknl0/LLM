"""Plain chat with the local LLM via Ollama."""

import ollama

from app.config import CHAT_MODEL

SYSTEM_PROMPT = (
    "You are a helpful local AI assistant running entirely on the user's "
    "own computer. Be concise and practical. You are good at coding."
)


def stream_chat(message: str, history: list[dict]):
    """Yield the assistant reply incrementally. `history` is a list of
    {"role", "content"} dicts as provided by gradio's chat component."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
