"""Approval-gated file editing — the Claude Code architecture: the
agent may READ files in your allowed folders and PROPOSE edits as
diffs, but nothing is written to disk until you approve it in the
Approvals tab. Approved edits back up the original first.

Allowed scope is EDIT_ROOTS in app/config.py (default: your home
folder). Backups land in data/backups/.
"""

import datetime
import difflib
import shutil
import uuid
from pathlib import Path

from app.config import BACKUPS_DIR, EDIT_ROOTS

MAX_READ_CHARS = 8000

_pending: dict[str, dict] = {}


def _allowed(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for root in EDIT_ROOTS:
        root = Path(root).resolve()
        if resolved == root or root in resolved.parents:
            return True
    return False


def read_file(path: str) -> str:
    """Agent tool: read a file inside the allowed folders."""
    target = Path(path).expanduser()
    if not _allowed(target):
        roots = ", ".join(str(r) for r in EDIT_ROOTS)
        return f"'{path}' is outside the allowed folders ({roots})."
    if not target.is_file():
        return f"No such file: {path}"
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Could not read {path}: {exc}"
    if len(text) > MAX_READ_CHARS:
        return text[:MAX_READ_CHARS] + f"\n... (truncated, file is {len(text)} chars)"
    return text or "(empty file)"


def propose_edit(path: str, new_content: str, reason: str = "") -> str:
    """Agent tool: queue a file edit for the user's approval."""
    target = Path(path).expanduser()
    if not _allowed(target):
        roots = ", ".join(str(r) for r in EDIT_ROOTS)
        return f"'{path}' is outside the allowed folders ({roots})."
    old = ""
    if target.is_file():
        try:
            old = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return f"Could not read current {path}: {exc}"
    diff = "\n".join(
        difflib.unified_diff(
            old.splitlines(), new_content.splitlines(),
            fromfile=f"current/{target.name}", tofile=f"proposed/{target.name}",
            lineterm="",
        )
    )
    if not diff:
        return "Proposed content is identical to the current file — nothing to do."
    edit_id = uuid.uuid4().hex[:8]
    _pending[edit_id] = {
        "path": str(target),
        "new_content": new_content,
        "reason": reason or "(no reason given)",
        "diff": diff,
    }
    return (
        f"Edit {edit_id} queued for {target}. Nothing is written yet — "
        "the user must approve the diff in the Approvals tab. Tell them so."
    )


def list_pending() -> list[tuple[str, str, str]]:
    return [
        (edit_id, item["path"], item["reason"])
        for edit_id, item in _pending.items()
    ]


def show_diff(edit_id: str) -> str:
    item = _pending.get((edit_id or "").strip())
    if not item:
        return "No pending edit with that ID — click Refresh."
    return (
        f"**{item['path']}**\n\nReason: {item['reason']}\n\n"
        f"```diff\n{item['diff'][:6000]}\n```"
    )


def approve(edit_id: str) -> str:
    item = _pending.pop((edit_id or "").strip(), None)
    if not item:
        return "No pending edit with that ID."
    target = Path(item["path"])
    note = ""
    if target.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = BACKUPS_DIR / f"{target.name}.{stamp}.bak"
        shutil.copy(target, backup)
        note = f" Original backed up to {backup}."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(item["new_content"], encoding="utf-8")
    return f"Applied edit to {target}.{note}"


def reject(edit_id: str) -> str:
    if _pending.pop((edit_id or "").strip(), None):
        return "Edit rejected and discarded."
    return "No pending edit with that ID."
