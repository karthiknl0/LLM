"""Project instruction discovery for local coding workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

INSTRUCTION_FILENAMES = (
    "CLAUDE.md",
    "AGENTS.md",
    ".agents.md",
    ".local-ai.md",
)


@dataclass(frozen=True)
class InstructionFile:
    path: str
    content: str


def _parents_from(start: Path, *, stop: Path | None = None) -> list[Path]:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    stop_resolved = stop.resolve() if stop else None
    paths: list[Path] = []
    while True:
        paths.append(current)
        if stop_resolved is not None and current == stop_resolved:
            break
        if current.parent == current:
            break
        current = current.parent
    return paths


def collect_project_instructions(
    start: str | Path = ".",
    *,
    max_bytes: int = 80_000,
) -> list[InstructionFile]:
    """Collect project instruction files from the current directory upward.

    Files nearer the filesystem root are returned first, then more specific
    files closer to `start`, so later instructions can refine earlier ones.
    """
    found: list[InstructionFile] = []
    total = 0
    for directory in reversed(_parents_from(Path(start))):
        for filename in INSTRUCTION_FILENAMES:
            path = directory / filename
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            total += len(text.encode("utf-8"))
            if total > max_bytes:
                raise ValueError(
                    f"Project instructions exceed {max_bytes} bytes. "
                    "Shorten instruction files or raise the limit."
                )
            found.append(InstructionFile(path=str(path), content=text))
    return found


def format_instructions(files: list[InstructionFile]) -> str:
    """Format instruction files for a system prompt."""
    if not files:
        return ""
    parts = ["Project instructions:"]
    for item in files:
        parts.append(f"\n--- {item.path} ---\n{item.content.strip()}")
    return "\n".join(parts).strip()
