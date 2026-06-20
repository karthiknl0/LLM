"""Shared model manager.

This layer sits above the runtime abstraction and centralizes model listing,
capability inference, default model checks, and pull/remove operations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import CHAT_MODEL, EMBED_MODEL, VISION_MODEL
from app.runtime import runtime


@dataclass(frozen=True)
class ModelInfo:
    """Normalized model metadata used by UI, CLI, API, and status checks."""

    name: str
    runtime: str
    capabilities: list[str]
    size: int | None = None
    modified_at: str | None = None
    family: str | None = None
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _details(raw: dict[str, Any]) -> dict[str, Any]:
    details = raw.get("details")
    return details if isinstance(details, dict) else {}


def _infer_capabilities(name: str, raw: dict[str, Any] | None = None) -> list[str]:
    """Infer broad capabilities from model name and runtime metadata.

    The goal is not perfect classification. It provides a useful default for
    filtering chat vs embedding models and for displaying model purpose.
    """
    raw = raw or {}
    lowered = name.lower()
    details = _details(raw)
    family = str(details.get("family") or "").lower()
    capabilities: set[str] = set()

    if "embed" in lowered or "embedding" in lowered or "embed" in family:
        capabilities.add("embedding")
    else:
        capabilities.add("chat")

    if any(token in lowered for token in ("vision", "vl", "llava", "bakllava")):
        capabilities.add("vision")

    if any(token in lowered for token in ("coder", "code", "codestral")):
        capabilities.add("code")

    if any(token in lowered for token in ("reason", "r1", "qwq")):
        capabilities.add("reasoning")

    if name == VISION_MODEL:
        capabilities.add("vision")
    if name == EMBED_MODEL:
        capabilities.add("embedding")
        capabilities.discard("chat")
    if name == CHAT_MODEL:
        capabilities.add("chat")

    return sorted(capabilities)


def _normalize(raw: dict[str, Any]) -> ModelInfo:
    name = raw.get("model") or raw.get("name") or raw.get("id") or "unknown"
    details = _details(raw)
    return ModelInfo(
        name=name,
        runtime=runtime().name,
        capabilities=_infer_capabilities(name, raw),
        size=raw.get("size"),
        modified_at=str(raw.get("modified_at")) if raw.get("modified_at") else None,
        family=details.get("family"),
        raw=raw,
    )


def list_models(*, include_embeddings: bool = True) -> list[ModelInfo]:
    """Return normalized installed model metadata."""
    models = [_normalize(raw) for raw in runtime().list_models()]
    if include_embeddings:
        return models
    return [m for m in models if "embedding" not in m.capabilities]


def installed_model_names(*, include_embeddings: bool = True) -> list[str]:
    """Return installed model names."""
    return sorted(m.name for m in list_models(include_embeddings=include_embeddings))


def chat_model_names() -> list[str]:
    """Return models appropriate for chat/model dropdowns."""
    return installed_model_names(include_embeddings=False)


def describe_model(name: str) -> ModelInfo | None:
    """Return metadata for one installed model, if present."""
    target = name.strip()
    for model in list_models(include_embeddings=True):
        if model.name == target:
            return model
    return None


def _is_present(installed: set[str], name: str) -> bool:
    return any(m == name or m.split(":")[0] == name for m in installed)


def default_model_checks() -> list[dict[str, Any]]:
    """Check whether configured default models are installed."""
    installed = set(installed_model_names(include_embeddings=True))
    checks = []
    for label, name, capability in (
        ("Chat model", CHAT_MODEL, "chat"),
        ("Vision model", VISION_MODEL, "vision"),
        ("Embedding model", EMBED_MODEL, "embedding"),
    ):
        present = _is_present(installed, name)
        checks.append(
            {
                "label": label,
                "name": name,
                "capability": capability,
                "present": present,
                "install_command": f"ollama pull {name}",
            }
        )
    return checks


def pull_model(name: str, *, stream: bool = True):
    """Pull/download a model through the configured runtime."""
    return runtime().pull_model(name, stream=stream)


def remove_model(name: str) -> Any:
    """Remove a model through the configured runtime."""
    return runtime().delete_model(name)
