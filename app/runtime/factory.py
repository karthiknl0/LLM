"""Runtime factory.

`AIHUB_RUNTIME` is reserved for future backend selection. The only supported
runtime today is Ollama.
"""

from __future__ import annotations

import os

from app.runtime.base import LLMRuntime
from app.runtime.ollama_runtime import OllamaRuntime

_RUNTIME: LLMRuntime | None = None


def runtime() -> LLMRuntime:
    """Return the configured model runtime singleton."""
    global _RUNTIME
    if _RUNTIME is not None:
        return _RUNTIME

    name = os.environ.get("AIHUB_RUNTIME", "ollama").strip().lower()
    if name != "ollama":
        raise ValueError(
            f"Unsupported AIHUB_RUNTIME={name!r}. Only 'ollama' is available today."
        )
    _RUNTIME = OllamaRuntime()
    return _RUNTIME
