"""Runtime model selection: which model is the active brain.
Defaults to config.CHAT_MODEL; the dropdown at the top of the UI (or
the /model command) switches it instantly for everything — chat,
agent, team, research, memory extraction.
"""

from app.core.config import CHAT_MODEL, ROOT
from app.runtime import runtime

# Remembers the chosen model across restarts so the dropdown doesn't
# snap back to the config default every launch.
_STATE_FILE = ROOT / "data" / "model.txt"


def _load() -> str:
    try:
        saved = _STATE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        saved = ""
    return saved or CHAT_MODEL


_current = _load()


def current_model() -> str:
    return _current


def set_model(name: str) -> str:
    global _current
    name = (name or "").strip()
    if not name:
        return f"Active model: `{_current}`"
    _current = name
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(name, encoding="utf-8")
    except OSError:
        pass  # in-memory selection still works if the disk write fails
    return f"Active model: `{name}`"


def installed_models() -> list[str]:
    """Chat-capable models pulled in the configured runtime.

    The primary model (qwen3.5:4b) also serves vision, so it must stay in
    this list — only dedicated embedding models are filtered out.
    """
    try:
        return runtime().list_model_names(include_embeddings=False)
    except Exception:
        return [_current]
