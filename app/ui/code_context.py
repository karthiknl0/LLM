"""UI helpers for project code context."""

from __future__ import annotations

from pathlib import Path

from app.local_code.editing import list_edits
from app.local_code.indexer import build_project_index, load_project_index, search_project_index
from app.local_code.instructions import collect_project_instructions


def index_project_for_code(project_folder: str) -> str:
    try:
        data = build_project_index(Path(project_folder or "."))
    except Exception as exc:
        return f"Could not index project: {exc}"
    return f"Indexed {len(data['files'])} file(s) from {data['project']}."


def instruction_summary(project_folder: str) -> str:
    try:
        files = collect_project_instructions(Path(project_folder or "."))
    except Exception as exc:
        return f"Could not read project instructions: {exc}"
    if not files:
        return "No project instruction files found. Add CLAUDE.md, AGENTS.md, .agents.md, or .local-ai.md."
    return "\n".join(f"- `{item.path}`" for item in files)


def code_index_summary(project_folder: str) -> str:
    try:
        data = load_project_index(Path(project_folder or "."))
    except Exception as exc:
        return f"Could not read code index: {exc}"
    if not data:
        return "No code index found yet."
    return f"Code index: {len(data.get('files', []))} file(s) for {data.get('project', project_folder)}."


def search_code_index(project_folder: str, query: str) -> str:
    query = (query or "").strip()
    if not query:
        return "Enter a search query."
    matches = search_project_index(Path(project_folder or "."), query)
    if not matches:
        return "No indexed matches. Index the project first or try another query."
    return "\n".join(f"- `{item.path}` ({item.size} bytes)" for item in matches)


def pending_code_edits_count() -> int:
    return len(list_edits())
