"""Runtime model selection: which Ollama model is the active brain.
Defaults to config.CHAT_MODEL; the dropdown at the top of the UI (or
the /model command) switches it instantly for everything — chat,
agent, team, research, memory extraction.
"""

from app.config import CHAT_MODEL, EMBED_MODEL, VISION_MODEL

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
    """Chat-capable models pulled in Ollama."""
    try:
        import ollama

        excluded = {
            EMBED_MODEL.split(":", 1)[0],
            VISION_MODEL.split(":", 1)[0],
        }
        names = sorted(
            m["model"] for m in ollama.list()["models"]
            if "embed" not in m["model"].lower()
            and m["model"].split(":", 1)[0] not in excluded
        )
    except Exception:
        return [_current]
    return names
