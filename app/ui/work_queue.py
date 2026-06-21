"""Work queue rows for UI."""

from __future__ import annotations

from app.local_code.editing import list_edits as list_code_items
from app.tools.file_ops import list_pending as list_agent_items


def rows() -> list[tuple[str, str, str, str]]:
    output: list[tuple[str, str, str, str]] = []
    for item_id, path, reason in list_agent_items():
        output.append(("agent", f"agent:{item_id}", path, reason))
    for item in list_code_items():
        output.append(("code", f"code:{item.id}", item.path, item.reason))
    return output
