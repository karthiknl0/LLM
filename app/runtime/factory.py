"""Runtime factory.

`AIHUB_RUNTIME` selects the model backend. Ollama is the only production-ready
runtime today. llama.cpp is recognized as a reserved placeholder so users get a
clear error if they try it before implementation is finished.
"""

from __future__ import annotations

import os

from app.runtime.base import LLMRuntime
from app.runtime.llamacpp_runtime import LlamaCppRuntime
from app.runtime.ollama_runtime import OllamaRuntime

_RUNTIME: LLMRuntime | None = None


def runtime() -> LLMRuntime:
    """Return the configured model runtime singleton."""
    global _RUNTIME
    if _RUNTIME is not None:
        return _RUNTIME

    name = os.environ.get("AIHUB_RUNTIME", "ollama").strip().lower()
    if name == "ollama":
        _RUNTIME = OllamaRuntime()
    elif name in {"llamacpp", "llama.cpp", "llama-cpp"}:
        _RUNTIME = LlamaCppRuntime()
    else:
        raise ValueError(
            f"Unsupported AIHUB_RUNTIME={name!r}. "
            "Supported values today: 'ollama'. Reserved: 'llamacpp'."
        )
    return _RUNTIME
