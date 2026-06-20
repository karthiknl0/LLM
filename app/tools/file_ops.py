"""Project file operations for the agent.

Inside the selected project, the agent can read, search, and edit directly;
existing files are backed up first. Files elsewhere remain approval-gated
and limited to EDIT_ROOTS. Backups land in data/backups/.
"""

import datetime
import difflib
import shutil
import uuid
from pathlib import Path

from app.core.config import BACKUPS_DIR, EDIT_ROOTS

from app.core.project import active_project_folder, is_inside_active_project
MAX_READ_CHARS = 8000
MAX_LIST_ENTRIES = 200
MAX_SEARCH_RESULTS = 80
SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build", ".idea", ".vscode",
}

_pending: dict[str, dict] = {}


def _resolve_path(path: str) -> Path:
    """Resolve relative tool paths from the active project root."""
    target = Path(path or ".").expanduser()
    if not target.is_absolute():
        target = active_project_folder() / target
    return target.resolve()


def _allowed(path: Path) -> bool:
    if is_inside_active_project(path):
        return True
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
    target = _resolve_path(path)
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


def list_files(path: str, depth: int = 2) -> str:
    """List a folder tree inside the allowed roots."""
    target = _resolve_path(path)
    if not _allowed(target):
        roots = ", ".join(str(r) for r in EDIT_ROOTS)
        return f"'{path}' is outside the allowed folders ({roots})."
    if not target.is_dir():
        return f"No such folder: {path}"
    depth = max(1, min(int(depth or 2), 5))
    entries = []
    try:
        for item in sorted(target.rglob("*")):
            relative = item.relative_to(target)
            if set(relative.parts) & SKIP_DIRS or len(relative.parts) > depth:
                continue
            entries.append(str(relative) + ("/" if item.is_dir() else ""))
            if len(entries) >= MAX_LIST_ENTRIES:
                entries.append("... (listing truncated)")
                break
    except OSError as exc:
        return f"Could not list {path}: {exc}"
    return f"Folder: {target.resolve()}\n" + ("\n".join(entries) or "(empty)")


def search_files(query: str, path: str) -> str:
    """Search filenames and text content under an allowed folder."""
    target = _resolve_path(path)
    if not _allowed(target):
        roots = ", ".join(str(r) for r in EDIT_ROOTS)
        return f"'{path}' is outside the allowed folders ({roots})."
    if not target.is_dir():
        return f"No such folder: {path}"
    needle = (query or "").strip().lower()
    if not needle:
        return "Provide a search query."

    results = []
    try:
        for item in sorted(target.rglob("*")):
            relative = item.relative_to(target)
            if not item.is_file() or set(relative.parts) & SKIP_DIRS:
                continue
            if needle in item.name.lower():
                results.append(f"{relative}: filename match")
            try:
                if item.stat().st_size > 1_000_000:
                    continue
                text = item.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                if needle in line.lower():
                    results.append(f"{relative}:{line_number}: {line.strip()[:240]}")
                    if len(results) >= MAX_SEARCH_RESULTS:
                        break
            if len(results) >= MAX_SEARCH_RESULTS:
                break
    except OSError as exc:
        return f"Could not search {path}: {exc}"
    if not results:
        return f"No matches for '{query}' under {target.resolve()}."
    if len(results) >= MAX_SEARCH_RESULTS:
        results.append("... (results truncated)")
    return "\n".join(results)


def propose_edit(path: str, new_content: str, reason: str = "") -> str:
    """Agent tool: queue a file edit for the user's approval."""
    target = _resolve_path(path)
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


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace one exact text block inside an active-project file."""
    target = _resolve_path(path)
    if not is_inside_active_project(target):
        return (
            f"'{path}' is outside the active project "
            f"({active_project_folder()})."
        )
    if not target.is_file():
        return f"No such file: {target}"
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        matches = content.count(old_text)
        if matches == 0:
            return "The exact old_text was not found; read the file and retry."
        if matches > 1:
            return (
                f"old_text matches {matches} places; provide a larger unique "
                "block so only the intended location changes."
            )
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = BACKUPS_DIR / f"{target.name}.{stamp}.bak"
        shutil.copy(target, backup)
        target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
    except OSError as exc:
        return f"Could not edit {target}: {exc}"
    return f"Edited {target}. Backup: {backup}."


def write_file(path: str, new_content: str) -> str:
    """Write a complete file directly inside the active project."""
    target = _resolve_path(path)
    if not is_inside_active_project(target):
        return (
            f"'{path}' is outside the active project "
            f"({active_project_folder()})."
        )
    try:
        if target.is_file():
            old = target.read_text(encoding="utf-8", errors="replace")
            if old == new_content:
                return f"{target} already has the requested content."
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup = BACKUPS_DIR / f"{target.name}.{stamp}.bak"
            shutil.copy(target, backup)
        else:
            backup = None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        return f"Could not write {target}: {exc}"
    note = f" Backup: {backup}." if backup else ""
    return f"Wrote {target}.{note}"


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
