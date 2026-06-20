"""Runtime interface for model backends."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol


class LLMRuntime(Protocol):
    """Backend interface used by Local AI Hub model callers."""

    name: str

    def list_models(self) -> list[dict[str, Any]]:
        """Return raw model metadata from the backend."""

    def list_model_names(self, *, include_embeddings: bool = True) -> list[str]:
        """Return installed model names."""

    def pull_model(self, name: str, *, stream: bool = True):
        """Pull or download a model."""

    def delete_model(self, name: str) -> Any:
        """Remove a model from the local backend."""

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run chat completion."""

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        stream: bool = False,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run text generation."""

    def embed(self, *, model: str, input: list[str]) -> list[list[float]]:
        """Return embeddings for input text."""
