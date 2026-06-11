"""Slash commands for the chat boxes — instant actions without leaving
the conversation, like Claude Code's / commands. Type /help to list
them. Messages that don't start with "/" go to the model as usual.
"""


def _fmt_rows(rows, empty: str) -> str:
    if not rows:
        return empty
    return "\n".join("- " + " — ".join(str(c) for c in row) for row in rows)


def _cmd_help(_arg: str) -> str:
    lines = [f"- **/{name}** {spec[0]}" for name, spec in COMMANDS.items()]
    return "**Commands**\n" + "\n".join(lines)


def _cmd_status(_arg: str) -> str:
    from app.status import run_checks

    return run_checks()


def _cmd_memory(_arg: str) -> str:
    from app.memory import list_memories

    return "**Memories & lessons**\n" + _fmt_rows(
        list_memories()[:25], "(nothing stored yet)"
    )


def _cmd_forget(_arg: str) -> str:
    from app.memory import clear_memories

    return clear_memories()


def _cmd_skills(_arg: str) -> str:
    from app.skills import list_skills

    return "**Self-built skills**\n" + _fmt_rows(
        list_skills(), "(none learned yet)"
    )


def _cmd_playbooks(_arg: str) -> str:
    from app.playbooks import catalog

    return "**Playbooks**\n" + _fmt_rows(catalog(), "(none)")


def _cmd_playbook(arg: str) -> str:
    from app.playbooks import load_playbook

    return load_playbook(arg) if arg else "Usage: /playbook <name>"


def _cmd_note(arg: str) -> str:
    from app.notes import take_note

    return take_note(arg) if arg else "Usage: /note <text>"


def _cmd_notes(_arg: str) -> str:
    from app.notes import read_notes

    return f"**Scratchpad**\n```\n{read_notes()}\n```"


def _cmd_index(_arg: str) -> str:
    from app.rag import index_documents

    return index_documents()


def _cmd_approvals(_arg: str) -> str:
    from app.fileedit import list_pending

    return "**Pending file edits** (review in the Approvals tab)\n" + _fmt_rows(
        list_pending(), "(none waiting)"
    )


def _cmd_loop(arg: str) -> str:
    from app.scheduler import start_loop

    minutes_str, _, prompt = arg.partition(" ")
    try:
        minutes = float(minutes_str)
    except ValueError:
        return "Usage: /loop <minutes> <prompt or /command>"
    return start_loop(minutes, prompt)


def _cmd_loops(_arg: str) -> str:
    from app.scheduler import list_loops

    return list_loops()


def _cmd_stoploop(arg: str) -> str:
    from app.scheduler import stop_loop

    return stop_loop(arg)


COMMANDS = {
    "help": ("— list available commands", _cmd_help),
    "status": ("— check Ollama, models, GPU, data", _cmd_status),
    "memory": ("— show stored memories and lessons", _cmd_memory),
    "forget": ("— erase all memories and lessons", _cmd_forget),
    "skills": ("— functions the agent taught itself", _cmd_skills),
    "playbooks": ("— list authored playbooks", _cmd_playbooks),
    "playbook": ("<name> — show one playbook", _cmd_playbook),
    "note": ("<text> — add to the scratchpad", _cmd_note),
    "notes": ("— show the scratchpad", _cmd_notes),
    "index": ("— (re)index data/documents/", _cmd_index),
    "approvals": ("— list file edits awaiting approval", _cmd_approvals),
    "compact": ("— summarize this chat; older turns leave the context", lambda a: "Type /compact directly in the chat box."),
    "loop": ("<minutes> <prompt> — run a prompt on a schedule", _cmd_loop),
    "loops": ("— list running loops", _cmd_loops),
    "stoploop": ("<id> — stop a loop", _cmd_stoploop),
}


def handle_command(message: str) -> str | None:
    """A reply if the message is a slash command, else None."""
    text = (message or "").strip()
    if not text.startswith("/"):
        return None
    name, _, arg = text[1:].partition(" ")
    name = name.lower()
    if name not in COMMANDS:
        return f"Unknown command `/{name}`.\n\n" + _cmd_help("")
    try:
        return COMMANDS[name][1](arg.strip())
    except Exception as exc:
        return f"/{name} failed: {exc}"
