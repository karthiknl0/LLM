"""Lightweight project indexing for Local Code."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import CODE_EXTENSIONS, LOCAL_CODE_INDEX_DIR

SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache", ".ruff_cache",
}
MAX_FILE_BYTES = 250_000
MAX_SNIPPET_CHARS = 1_200


@dataclass(frozen=True)
class IndexedFile:
    path: str
    size: int
    mtime: float
    snippet: str


def project_key(project: str | Path) -> str:
    return hashlib.sha256(str(Path(project).resolve()).encode("utf-8")).hexdigest()[:16]


def index_path(project: str | Path) -> Path:
    return LOCAL_CODE_INDEX_DIR / f"{project_key(project)}.json"


def _iter_files(project: Path):
    for path in sorted(project.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(project)
        if set(rel.parts) & SKIP_DIRS:
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path


def _snippet(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:MAX_SNIPPET_CHARS]


def build_project_index(project: str | Path) -> dict[str, Any]:
    """Scan a project and write a compact JSON index."""
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Project folder not found: {root}")
    files: list[dict[str, Any]] = []
    for path in _iter_files(root):
        try:
            stat = path.stat()
            files.append(
                {
                    "path": str(path.relative_to(root)),
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "snippet": _snippet(path),
                }
            )
        except OSError:
            continue
    data = {"project": str(root), "files": files}
    index_path(root).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def load_project_index(project: str | Path) -> dict[str, Any] | None:
    path = index_path(project)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def search_project_index(project: str | Path, query: str, *, limit: int = 8) -> list[IndexedFile]:
    """Search indexed paths and snippets by simple token scoring."""
    data = load_project_index(project)
    if not data:
        return []
    tokens = [t.lower() for t in query.split() if len(t) >= 2]
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in data.get("files", []):
        haystack = f"{item.get('path', '')}\n{item.get('snippet', '')}".lower()
        score = sum(haystack.count(token) for token in tokens)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda row: (-row[0], row[1].get("path", "")))
    return [
        IndexedFile(
            path=str(item.get("path", "")),
            size=int(item.get("size", 0)),
            mtime=float(item.get("mtime", 0.0)),
            snippet=str(item.get("snippet", "")),
        )
        for _score, item in scored[:limit]
    ]


def format_index_context(matches: list[IndexedFile]) -> str:
    if not matches:
        return ""
    parts = ["Relevant indexed project files:"]
    for item in matches:
        parts.append(f"\n--- {item.path} ---\n{item.snippet.strip()}")
    return "\n".join(parts).strip()
