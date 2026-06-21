"""Work queue rows for UI."""

from __future__ import annotations

from app.local_code import editing as code_items
from app.tools import file_ops as agent_items


def rows() -> list[tuple[str, str, str, str]]:
    output: list[tuple[str, str, str, str]] = []
    for item_id, path, reason in agent_items.list_pending():
        output.append(("agent", f"agent:{item_id}", path, reason))
    for item in code_items.list_edits():
        output.append(("code", f"code:{item.id}", item.path, item.reason))
    return output


def _split(value: str) -> tuple[str, str]:
    text = (value or "").strip()
    if ":" not in text:
        return "agent", text
    left, right = text.split(":", 1)
    return left.strip().lower(), right.strip()


def show(value: str) -> str:
    kind, item_id = _split(value)
    if kind == "code":
        try:
            return "```diff\n" + code_items.show_edit(item_id)[:8000] + "\n```"
        except Exception as exc:
            return f"No code item found: {exc}"
    return agent_items.show_diff(item_id)


def accept(value: str) -> str:
    kind, item_id = _split(value)
    if kind == "code":
        try:
            return code_items.apply_edit(item_id)
        except Exception as exc:
            return f"Could not apply code item: {exc}"
    return agent_items.approve(item_id)


def drop(value: str) -> str:
    kind, item_id = _split(value)
    if kind == "code":
        try:
            return code_items.reject_edit(item_id)
        except Exception as exc:
            return f"Could not drop code item: {exc}"
    return agent_items.reject(item_id)
