"""Chat with the local LLM via Ollama, with long-term memory.

Every turn is also logged to data/chatlogs/ so your conversations can
later be used to fine-tune your own model (see finetune/README.md).
"""

import datetime
import json

import ollama

from app.commands import handle_command
from app.core.config import CHATLOG_DIR
from app.session.modelstate import current_model
from app.chat.history import compact_history
from app.content.instructions import standing_instructions
from app.memory import recall, recall_lessons, remember
from app.personas.manager import DEFAULT_NAME, get_prompt


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


def stream_chat(message: str, history: list[dict], persona: str = DEFAULT_NAME):
    """Yield the assistant reply incrementally. `history` is a list of
    {"role", "content"} dicts as provided by gradio's chat component."""
    if message.strip().lower() == "/compact":
        from app.chat.history import manual_compact

        yield manual_compact(history)
        return
    if message.strip().lower() == "/export":
        from app.commands import export_chat

        yield export_chat(history)
        return
    command_reply = handle_command(message)
    if command_reply is not None:
        yield command_reply
        return

    system = get_prompt(persona) or SYSTEM_PROMPT
    rules = standing_instructions()
    if rules:
        system += "\n\nThe user's standing instructions (always follow):\n" + rules
    memories = recall(message)
    if memories:
        system += "\n\nThings you remember about the user from past chats:\n"
        system += "\n".join(f"- {m}" for m in memories)
    lessons = recall_lessons(message)
    if lessons:
        system += "\n\nStanding instructions learned from past corrections:\n"
        system += "\n".join(f"- {lesson}" for lesson in lessons)

    summary, past_messages = compact_history(history)
    if summary:
        system += "\n\nSummary of earlier parts of this conversation:\n" + summary
    messages = [{"role": "system", "content": system}] + past_messages
    messages.append({"role": "user", "content": message})

    reply = ""
    for part in ollama.chat(
        model=current_model(), messages=messages, stream=True, think=False
    ):
        reply += part["message"]["content"]
        yield reply

    # after the reply finishes, log it and store anything worth remembering
    _log_turn(message, reply)
    remember(message, reply)
    from app.services.hooks import post_reply

    post_reply(reply)
