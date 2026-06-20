"""Runtime abstraction for Local AI Hub.

Use `runtime()` for all model operations so UI, CLI, API, RAG, and agents can
share one backend interface. Ollama is the default runtime today; llama.cpp,
vLLM, or Transformers can be added later without rewriting callers.
"""

from app.runtime.base import LLMRuntime
from app.runtime.factory import runtime
from app.runtime.ollama_runtime import OllamaRuntime

__all__ = ["LLMRuntime", "OllamaRuntime", "runtime"]
