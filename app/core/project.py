"""Track the folder selected for the current agent task."""

from pathlib import Path

from app.core.config import WORKSPACE_DIR


_active_project_dir: Path | None = None


def set_project_folder(path: str | None) -> tuple[bool, str]:
    """Select a project folder, or reset to the internal workspace."""
    global _active_project_dir
    if not (path or "").strip():
        _active_project_dir = None
        return True, f"Using default workspace: {WORKSPACE_DIR}"
    target = Path(path).expanduser()
    try:
        resolved = target.resolve()
    except OSError as exc:
        return False, f"Could not resolve project folder: {exc}"
    if not resolved.exists():
        return False, f"Project folder does not exist: {resolved}"
    if not resolved.is_dir():
        return False, f"Project path is not a folder: {resolved}"
    _active_project_dir = resolved
    return True, f"Active project folder: {resolved}"


def active_project_folder(default: Path | None = None) -> Path:
    return _active_project_dir or default or WORKSPACE_DIR


def active_project_label() -> str:
    return str(active_project_folder())


def is_inside_active_project(path: Path) -> bool:
    try:
        resolved = path.resolve()
        root = active_project_folder().resolve()
    except OSError:
        return False
    return resolved == root or root in resolved.parents
