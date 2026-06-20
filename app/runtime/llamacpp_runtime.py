"""llama.cpp runtime placeholder with GGUF model discovery.

This runtime can list local `.gguf` files from `data/gguf/`. Inference is not
implemented yet, so chat/generate/embed still raise clear errors.
"""

from __future__ import annotations

from typing import Any

from app.core.config import GGUF_MODELS_DIR


class LlamaCppRuntime:
    """Future runtime adapter for llama.cpp-compatible local models."""

    name = "llamacpp"

    def _not_ready(self):
        raise NotImplementedError(
            "AIHUB_RUNTIME=llamacpp can discover GGUF files but inference "
            "is not implemented yet. Use AIHUB_RUNTIME=ollama for chat."
        )

    def _gguf_files(self):
        if not GGUF_MODELS_DIR.exists():
            return []
        return sorted(path for path in GGUF_MODELS_DIR.rglob("*.gguf") if path.is_file())

    def list_models(self) -> list[dict[str, Any]]:
        models: list[dict[str, Any]] = []
        for path in self._gguf_files():
            rel = path.relative_to(GGUF_MODELS_DIR)
            name = str(rel.with_suffix(""))
            models.append(
                {
                    "model": name,
                    "name": name,
                    "path": str(rel),
                    "size": path.stat().st_size,
                    "modified_at": path.stat().st_mtime,
                    "details": {
                        "family": "gguf",
                        "format": "gguf",
                    },
                }
            )
        return models

    def list_model_names(self, *, include_embeddings: bool = True) -> list[str]:
        names = [m["model"] for m in self.list_models()]
        if not include_embeddings:
            names = [name for name in names if "embed" not in name.lower()]
        return sorted(names)

    def pull_model(self, name: str, *, stream: bool = True):
        raise NotImplementedError(
            "llama.cpp runtime does not pull models yet. Place .gguf files in data/gguf/."
        )

    def delete_model(self, name: str) -> Any:
        raise NotImplementedError(
            "llama.cpp runtime does not delete models yet. Remove the .gguf file manually."
        )

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
