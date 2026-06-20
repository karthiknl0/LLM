"""LocalModel.yaml package loader.

A LocalModel package is a named preset that points to a base runtime model and
adds default system prompt, generation parameters, capabilities, and future RAG
or tool configuration.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.core.config import ROOT

PACKAGES_DIR = ROOT / "data" / "models"
PACKAGE_FILENAMES = ("LocalModel.yaml", "LocalModel.yml", "localmodel.yaml", "localmodel.yml")


@dataclass(frozen=True)
class LocalModelPackage:
    name: str
    base: str
    path: str
    system: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    rag: dict[str, Any] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _package_paths() -> list[Path]:
    paths: list[Path] = []
    for filename in PACKAGE_FILENAMES:
        root_file = ROOT / filename
        if root_file.is_file():
            paths.append(root_file)
    if PACKAGES_DIR.exists():
        for filename in PACKAGE_FILENAMES:
            paths.extend(sorted(PACKAGES_DIR.rglob(filename)))
    return paths


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _load_path(path: Path) -> LocalModelPackage:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")

    name = str(data.get("name") or path.parent.name).strip()
    base = str(data.get("base") or data.get("model") or "").strip()
    if not name:
        raise ValueError(f"{path} is missing required field: name")
    if not base:
        raise ValueError(f"{path} is missing required field: base")

    parameters = data.get("parameters") or {}
    if not isinstance(parameters, dict):
        raise ValueError(f"{path} field 'parameters' must be a mapping")

    rag = data.get("rag") or {}
    if not isinstance(rag, dict):
        raise ValueError(f"{path} field 'rag' must be a mapping")

    return LocalModelPackage(
        name=name,
        base=base,
        path=_display_path(path),
        system=str(data.get("system") or ""),
        parameters=parameters,
        capabilities=_as_list(data.get("capabilities")),
        rag=rag,
        tools=_as_list(data.get("tools")),
        description=str(data.get("description") or ""),
    )


def load_package_file(path: str | Path) -> LocalModelPackage:
    """Validate and load one LocalModel file by path."""
    return _load_path(Path(path).expanduser().resolve())


def list_packages() -> list[LocalModelPackage]:
    """Return all valid LocalModel packages, sorted by name."""
    packages: list[LocalModelPackage] = []
    seen: set[str] = set()
    for path in _package_paths():
        package = _load_path(path)
        if package.name in seen:
            continue
        seen.add(package.name)
        packages.append(package)
    return sorted(packages, key=lambda p: p.name)


def load_package(name: str) -> LocalModelPackage | None:
    """Load a package by package name."""
    target = name.strip()
    for package in list_packages():
        if package.name == target:
            return package
    return None


def resolve_model_or_package(name: str | None) -> tuple[str, LocalModelPackage | None]:
    """Resolve a CLI/API model value to a base runtime model plus package.

    If `name` matches a LocalModel package, return the package base and package.
    Otherwise return the name unchanged and no package. If name is empty, callers
    should apply their existing default before calling this function.
    """
    if not name:
        return "", None
    package = load_package(name)
    if package is not None:
        return package.base, package
    return name, None


def package_options(package: LocalModelPackage | None, extra: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Merge package parameters with request/runtime options."""
    merged: dict[str, Any] = {}
    if package:
        merged.update(package.parameters)
    if extra:
        merged.update(extra)
    return merged or None


def package_messages(
    package: LocalModelPackage | None,
    messages: list[dict[str, Any]],
    fallback_system: str | None = None,
) -> list[dict[str, Any]]:
    """Apply package system prompt to a chat message list.

    If the first message is already a system message, the package system is
    prepended to that content. Otherwise a system message is inserted.
    """
    system = ""
    if fallback_system:
        system = fallback_system
    if package and package.system:
        system = f"{package.system}\n\n{system}" if system else package.system
    if not system:
        return messages

    prepared = [dict(m) for m in messages]
    if prepared and prepared[0].get("role") == "system":
        prepared[0]["content"] = f"{system}\n\n{prepared[0].get('content', '')}".strip()
    else:
        prepared.insert(0, {"role": "system", "content": system})
    return prepared
