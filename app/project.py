"""Active project folder for agent work.

The app still has an internal workspace for scratch files, but coding-agent
tools should operate on the folder the user selected for the current task.
"""

from pathlib import Path

from app.config import WORKSPACE_DIR

_active_project_dir: Path | None = None


def set_project_folder(path: str | None) -> tuple[bool, str]:
    """Set the active project folder for this app process."""
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
    """Return the selected project folder, or the app workspace default."""
    return _active_project_dir or default or WORKSPACE_DIR


def active_project_label() -> str:
    return str(active_project_folder())


def is_inside_active_project(path: Path) -> bool:
    """True when path is inside the current project folder."""
    try:
        resolved = path.resolve()
        root = active_project_folder().resolve()
    except OSError:
        return False
    return resolved == root or root in resolved.parents
