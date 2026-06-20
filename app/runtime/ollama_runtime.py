"""Ollama runtime implementation."""

from __future__ import annotations

from typing import Any

import ollama


class OllamaRuntime:
    """Runtime adapter around the official Ollama Python client."""

    name = "ollama"

    def list_models(self) -> list[dict[str, Any]]:
        return ollama.list()["models"]

    def list_raw(self) -> dict[str, Any]:
        """Return the raw Ollama list response for Ollama-compatible APIs."""
        return ollama.list()

    def list_model_names(self, *, include_embeddings: bool = True) -> list[str]:
        names = [m["model"] for m in self.list_models()]
        if not include_embeddings:
            names = [name for name in names if "embed" not in name.lower()]
        return sorted(names)

    def pull_model(self, name: str, *, stream: bool = True):
        return ollama.pull(name, stream=stream)

    def delete_model(self, name: str) -> Any:
        return ollama.delete(name)

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        if options is not None:
            kwargs["options"] = options
        return ollama.chat(model=model, messages=messages, stream=stream, **kwargs)

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        stream: bool = False,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        if options is not None:
            kwargs["options"] = options
        return ollama.generate(model=model, prompt=prompt, stream=stream, **kwargs)

    def embed(self, *, model: str, input: list[str]) -> list[list[float]]:
        return ollama.embed(model=model, input=input)["embeddings"]
