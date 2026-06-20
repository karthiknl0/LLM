"""llama.cpp runtime with GGUF discovery and optional inference.

This runtime lists local `.gguf` files from `data/gguf/`. If the optional
`llama-cpp-python` package is installed, it can run generate/chat calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import (
    GGUF_MODELS_DIR,
    LLAMACPP_N_CTX,
    LLAMACPP_N_GPU_LAYERS,
    LLAMACPP_VERBOSE,
)


class LlamaCppRuntime:
    """Runtime adapter for llama.cpp-compatible local GGUF models."""

    name = "llamacpp"

    def __init__(self) -> None:
        self._loaded: dict[str, Any] = {}

    def _gguf_files(self) -> list[Path]:
        if not GGUF_MODELS_DIR.exists():
            return []
        return sorted(path for path in GGUF_MODELS_DIR.rglob("*.gguf") if path.is_file())

    def _model_path(self, model: str) -> Path:
        target = model.strip()
        for path in self._gguf_files():
            rel = path.relative_to(GGUF_MODELS_DIR)
            name = str(rel.with_suffix(""))
            if target in {name, str(rel), path.name, path.stem}:
                return path
        raise FileNotFoundError(
            f"GGUF model {model!r} not found in {GGUF_MODELS_DIR}. "
            "Copy a .gguf file there or use `local-ai list` to see available names."
        )

    def _load(self, model: str):
        path = self._model_path(model)
        key = str(path)
        if key in self._loaded:
            return self._loaded[key]
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "AIHUB_RUNTIME=llamacpp requires optional package `llama-cpp-python`. "
                "Install it in your environment, then retry."
            ) from exc
        llm = Llama(
            model_path=str(path),
            n_ctx=LLAMACPP_N_CTX,
            n_gpu_layers=LLAMACPP_N_GPU_LAYERS,
            verbose=LLAMACPP_VERBOSE,
        )
        self._loaded[key] = llm
        return llm

    def list_models(self) -> list[dict[str, Any]]:
        models: list[dict[str, Any]] = []
        for path in self._gguf_files():
            rel = path.relative_to(GGUF_MODELS_DIR)
            name = str(rel.with_suffix(""))
            stat = path.stat()
            models.append(
                {
                    "model": name,
                    "name": name,
                    "path": str(rel),
                    "size": stat.st_size,
                    "modified_at": stat.st_mtime,
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
        llm = self._load(model)
        params = dict(options or {})
        params.update(kwargs)
        response = llm.create_chat_completion(
            messages=messages,
            stream=stream,
            **params,
        )
        if not stream:
            content = response["choices"][0]["message"].get("content", "")
            return {
                "model": model,
                "message": {"role": "assistant", "content": content},
                "done": True,
                "raw": response,
            }

        def events():
            for part in response:
                delta = part.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield {
                        "model": model,
                        "message": {"role": "assistant", "content": content},
                        "done": False,
                        "raw": part,
                    }
            yield {"model": model, "message": {"role": "assistant", "content": ""}, "done": True}

        return events()

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        stream: bool = False,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        llm = self._load(model)
        params = dict(options or {})
        params.update(kwargs)
        response = llm.create_completion(prompt=prompt, stream=stream, **params)
        if not stream:
            text = response["choices"][0].get("text", "")
            return {"model": model, "response": text, "done": True, "raw": response}

        def events():
            for part in response:
                text = part.get("choices", [{}])[0].get("text", "")
                if text:
                    yield {"model": model, "response": text, "done": False, "raw": part}
            yield {"model": model, "response": "", "done": True}

        return events()

    def embed(self, *, model: str, input: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "llama.cpp embedding support is not implemented yet. Use the default runtime for RAG."
        )
