# Runtime Abstraction

Local AI Hub routes core model operations through `app.runtime` instead of importing a backend client directly in every feature.

This prepares the project for multiple local backends while keeping the default backend stable.

## Current production backend

The production backend is `OllamaRuntime`.

It provides these operations:

```python
list_models()
list_model_names(include_embeddings=True)
pull_model(name, stream=True)
delete_model(name)
chat(model=..., messages=..., stream=False, options=None, **kwargs)
generate(model=..., prompt=..., stream=False, options=None, **kwargs)
embed(model=..., input=[...])
```

## Reserved llama.cpp backend

`LlamaCppRuntime` is present as a reserved future backend.

Current behavior:

- Discovers `.gguf` files in `data/gguf/`.
- Lists discovered files through the model manager and CLI.
- Does not run inference yet.
- Raises a clear `NotImplementedError` for chat, generate, embed, pull, and delete.

Try discovery:

```bash
mkdir -p data/gguf
# copy a .gguf model file into data/gguf/
AIHUB_RUNTIME=llamacpp local-ai list
```

Do not use `AIHUB_RUNTIME=llamacpp` for chat yet.

## Usage

```python
from app.runtime import runtime

response = runtime().chat(
    model="qwen3.5:4b",
    messages=[{"role": "user", "content": "Hello"}],
    stream=False,
)

vectors = runtime().embed(
    model="nomic-embed-text",
    input=["document text"],
)
```

## Environment variable

```bash
AIHUB_RUNTIME=ollama
AIHUB_RUNTIME=llamacpp
```

`ollama` is the working default. `llamacpp` is discovery-only for now.

## Migrated callers

These core surfaces use the runtime layer:

- `app/chat/stream.py`
- `app/rag/index.py`
- `app/rag/query.py`
- `app/session/modelstate.py`
- `app/session/status.py`
- `app/cli.py`
- `app/api/server.py`

## Next roadmap step

Implement non-streaming generation in `LlamaCppRuntime`, guarded by tests and optional dependencies so CI remains lightweight.
