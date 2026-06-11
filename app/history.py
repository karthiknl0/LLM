"""Long-conversation compaction: when a chat outgrows the model's
comfortable context, older turns are summarized and recent turns kept
verbatim — so nothing gets silently truncated away. (Claude Code's
context-compression pattern, reduced to one layer.)
"""

import re

import ollama

from app.config import CHAT_MODEL

MAX_HISTORY_CHARS = 12_000   # roughly a third of the context window
KEEP_RECENT_MESSAGES = 8     # always kept word-for-word

# Reply prefix of a manual /compact — later turns drop everything above it
COMPACT_MARKER = "📦 **Conversation compacted.**"

SUMMARY_PROMPT = (
    "Summarize this earlier part of a conversation in under 200 words. "
    "Keep decisions, facts, names, numbers, file names, and open "
    "questions — drop pleasantries and repetition.\n\n{transcript}"
)


def _summarize(messages: list[dict]) -> str | None:
    transcript = "\n\n".join(
        f"{m['role'].upper()}: {m['content'][:1200]}" for m in messages
    )[:10_000]
    try:
        response = ollama.chat(
            model=CHAT_MODEL,
            messages=[
                {"role": "user", "content": SUMMARY_PROMPT.format(transcript=transcript)}
            ],
        )
        summary = re.sub(
            r"<think>.*?</think>", "", response["message"]["content"], flags=re.DOTALL
        ).strip()
        return summary or None
    except Exception as exc:
        print(f"[history] summarization failed: {exc}")
        return None


def manual_compact(history: list[dict]) -> str:
    """The /compact command: summarize the whole conversation so far.
    The reply (marker + summary) stays in the chat; subsequent turns
    drop everything above the marker from the model's context."""
    messages = _clean(history)
    if not messages:
        return "Nothing to compact yet — the conversation is empty."
    summary = _summarize(messages)
    if not summary:
        return "Compaction failed (is Ollama running?) — nothing was changed."
    return (
        f"{COMPACT_MARKER} Older turns are dropped from the model's "
        f"context from here on; this summary replaces them:\n\n{summary}"
    )


def _clean(history: list[dict]) -> list[dict]:
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)
    ]
    # honor the most recent manual /compact: keep the marker (it holds
    # the summary), drop everything before it
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "assistant" and messages[i]["content"].startswith(
            COMPACT_MARKER
        ):
            return messages[i:]
    return messages


def compact_history(history: list[dict]) -> tuple[str | None, list[dict]]:
    """Return (summary_of_older_turns_or_None, messages_to_keep)."""
    messages = _clean(history)
    if sum(len(m["content"]) for m in messages) <= MAX_HISTORY_CHARS:
        return None, messages
    older = messages[:-KEEP_RECENT_MESSAGES]
    recent = messages[-KEEP_RECENT_MESSAGES:]
    if not older:
        return None, messages
    summary = _summarize(older)
    if summary is None:
        return None, messages
    return summary, recent
