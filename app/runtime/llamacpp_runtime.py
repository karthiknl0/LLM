"""llama.cpp runtime placeholder.

This file reserves the adapter shape for a future direct GGUF backend. The
runtime is not enabled by default.
"""

from __future__ import annotations

from typing import Any


class LlamaCppRuntime:
    """Future runtime adapter for llama.cpp-compatible local models."""

    name = "llamacpp"

    def _not_ready(self):
        raise NotImplementedError(
            "AIHUB_RUNTIME=llamacpp is not implemented yet. "
            "Use AIHUB_RUNTIME=ollama for now."
        )

    def list_models(self) -> list[dict[str, Any]]:
        self._not_ready()

    def list_model_names(self, *, include_embeddings: bool = True) -> list[str]:
        self._not_ready()

    def pull_model(self, name: str, *, stream: bool = True):
        self._not_ready()

    def delete_model(self, name: str) -> Any:
        self._not_ready()

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        self._not_ready()

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        stream: bool = False,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        self._not_ready()

    def embed(self, *, model: str, input: list[str]) -> list[list[float]]:
        self._not_ready()
