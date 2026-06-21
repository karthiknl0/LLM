"""Persistent approval queue for Local Code file edits."""

from __future__ import annotations

import datetime as _dt
import difflib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import BACKUPS_DIR, LOCAL_CODE_EDITS_DIR


@dataclass(frozen=True)
class PendingEdit:
    id: str
    project: str
    path: str
    reason: str
    diff: str


def _edit_file(edit_id: str) -> Path:
    return LOCAL_CODE_EDITS_DIR / f"{edit_id}.json"


def _resolve_project_file(project: str | Path, path: str | Path) -> Path:
    root = Path(project).expanduser().resolve()
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"{target} is outside project {root}")
    return target


def _load(edit_id: str) -> dict[str, Any]:
    path = _edit_file(edit_id.strip())
    if not path.is_file():
        raise FileNotFoundError(f"No pending edit: {edit_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def propose_file(project: str | Path, path: str | Path, new_content: str, *, reason: str = "") -> PendingEdit:
    """Queue a complete-file replacement for later approval."""
    root = Path(project).expanduser().resolve()
    target = _resolve_project_file(root, path)
    old_content = ""
    if target.exists():
        old_content = target.read_text(encoding="utf-8", errors="replace")
    diff = "\n".join(
        difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            fromfile=f"current/{target.relative_to(root)}",
            tofile=f"proposed/{target.relative_to(root)}",
            lineterm="",
        )
    )
    if not diff:
        raise ValueError("Proposed content is identical to the current file")
    edit_id = uuid.uuid4().hex[:8]
    payload = {
        "id": edit_id,
        "project": str(root),
        "path": str(target.relative_to(root)),
        "absolute_path": str(target),
        "reason": reason or "(no reason given)",
        "new_content": new_content,
        "diff": diff,
        "created_at": _dt.datetime.utcnow().isoformat() + "Z",
    }
    _edit_file(edit_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return PendingEdit(edit_id, str(root), payload["path"], payload["reason"], diff)


def list_edits() -> list[PendingEdit]:
    edits: list[PendingEdit] = []
    for path in sorted(LOCAL_CODE_EDITS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            edits.append(
                PendingEdit(
                    id=str(data["id"]),
                    project=str(data["project"]),
                    path=str(data["path"]),
                    reason=str(data.get("reason") or ""),
                    diff=str(data.get("diff") or ""),
                )
            )
        except (OSError, KeyError, json.JSONDecodeError):
            continue
    return edits


def show_edit(edit_id: str) -> str:
    data = _load(edit_id)
    return str(data.get("diff") or "")


def apply_edit(edit_id: str) -> str:
    data = _load(edit_id)
    target = Path(data["absolute_path"])
    if target.exists():
        stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = BACKUPS_DIR / f"{target.name}.{stamp}.bak"
        backup.write_text(target.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        backup_note = f" Backup: {backup}."
    else:
        backup_note = ""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(data["new_content"]), encoding="utf-8")
    _edit_file(str(data["id"])).unlink(missing_ok=True)
    return f"Applied edit {data['id']} to {target}.{backup_note}"


def reject_edit(edit_id: str) -> str:
    data = _load(edit_id)
    _edit_file(str(data["id"])).unlink(missing_ok=True)
    return f"Rejected edit {data['id']}."
