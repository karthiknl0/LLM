"""Runtime model selection: which Ollama model is the active brain.
Defaults to config.CHAT_MODEL; the dropdown at the top of the UI (or
the /model command) switches it instantly for everything — chat,
agent, team, research, memory extraction.
"""

from app.config import CHAT_MODEL

_current = CHAT_MODEL


def current_model() -> str:
    return _current


def set_model(name: str) -> str:
    global _current
    name = (name or "").strip()
    if not name:
        return f"Active model: `{_current}`"
    _current = name
    return f"Active model: `{name}`"


def installed_models() -> list[str]:
    """Chat-capable models pulled in Ollama (embedding models hidden)."""
    try:
        import ollama

        names = sorted(
            m["model"] for m in ollama.list()["models"]
            if "embed" not in m["model"]
        )
    except Exception:
        names = []
    if _current not in names:
        names.insert(0, _current)
    return names
