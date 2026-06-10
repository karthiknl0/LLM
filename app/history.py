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

SUMMARY_PROMPT = (
    "Summarize this earlier part of a conversation in under 200 words. "
    "Keep decisions, facts, names, numbers, file names, and open "
    "questions — drop pleasantries and repetition.\n\n{transcript}"
)


def compact_history(history: list[dict]) -> tuple[str | None, list[dict]]:
    """Return (summary_of_older_turns_or_None, messages_to_keep)."""
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)
    ]
    if sum(len(m["content"]) for m in messages) <= MAX_HISTORY_CHARS:
        return None, messages
    older = messages[:-KEEP_RECENT_MESSAGES]
    recent = messages[-KEEP_RECENT_MESSAGES:]
    if not older:
        return None, messages

    transcript = "\n\n".join(
        f"{m['role'].upper()}: {m['content'][:1200]}" for m in older
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
        return (summary or None), recent
    except Exception as exc:
        print(f"[history] compaction failed: {exc}")
        return None, messages
