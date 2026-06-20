# Runtime Abstraction

Local AI Hub now routes core model operations through `app.runtime` instead of importing a backend client directly in every feature.

This prepares the project for future backends while keeping Ollama as the default today.

## Current backend

The implemented backend is `OllamaRuntime`.

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

`AIHUB_RUNTIME` is reserved for backend selection:

```bash
AIHUB_RUNTIME=ollama
```

At the moment, only `ollama` is supported.

## Migrated callers

These core surfaces now use the runtime layer:

- `app/chat/stream.py`
- `app/rag/index.py`
- `app/rag/query.py`
- `app/session/modelstate.py`
- `app/session/status.py`
- `app/cli.py`
- `app/api/server.py`

## Next roadmap step

Add a model manager module on top of the runtime layer. It should centralize installed model listing, model capabilities, default model checks, pull/remove operations, and local metadata storage.
