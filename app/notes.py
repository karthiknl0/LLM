"""Structured note-taking for long tasks: the agent jots progress,
decisions, and next steps into a persistent scratchpad it can re-read
later — working state that survives context compaction. (One of the
three long-horizon techniques from Anthropic's context-engineering
guidance, alongside compaction and sub-agents.)
"""

import datetime

from app.config import WORKSPACE_DIR

NOTES_PATH = WORKSPACE_DIR / "NOTES.md"
MAX_INJECT_CHARS = 1500   # tail of notes shown in the system prompt
MAX_READ_CHARS = 8000


def take_note(text: str) -> str:
    if not (text or "").strip():
        return "Nothing to note."
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with NOTES_PATH.open("a", encoding="utf-8") as f:
        f.write(f"- [{stamp}] {text.strip()}\n")
    return "Noted."


def read_notes() -> str:
    if not NOTES_PATH.exists():
        return "(no notes yet)"
    return NOTES_PATH.read_text(encoding="utf-8")[-MAX_READ_CHARS:]


def recent_notes() -> str:
    """Tail of the scratchpad, for system-prompt injection."""
    if not NOTES_PATH.exists():
        return ""
    return NOTES_PATH.read_text(encoding="utf-8")[-MAX_INJECT_CHARS:].strip()
