# Model Manager

The model manager centralizes installed model metadata, capability inference, default model checks, and model pull/remove operations.

It lives in:

```text
app/models/manager.py
```

## Why it exists

Before this layer, each surface had to decide for itself how to list models, hide embedding models, check defaults, and call pull/remove operations.

Now the UI, CLI, API, and status checks can use one model source on top of the runtime abstraction.

## Main functions

```python
from app.models import (
    list_models,
    installed_model_names,
    chat_model_names,
    describe_model,
    default_model_checks,
    pull_model,
    remove_model,
)
```

### List normalized models

```python
models = list_models(include_embeddings=True)
```

Each item is a `ModelInfo` dataclass:

```python
ModelInfo(
    name="qwen3.5:4b",
    runtime="ollama",
    capabilities=["chat", "vision"],
    size=..., 
    modified_at="...",
    family="...",
    raw={...},
)
```

### Chat model names

```python
names = chat_model_names()
```

This hides embedding-only models from chat dropdowns and chat APIs.

### Inspect one model

```python
model = describe_model("qwen3.5:4b")
```

### Default checks

```python
checks = default_model_checks()
```

This reports whether the configured chat, vision, and embedding defaults are installed.

## Capability inference

Capabilities are inferred from model name, runtime metadata, and configured defaults.

Current capabilities:

- `chat`
- `embedding`
- `vision`
- `code`
- `reasoning`

The inference is intentionally simple and safe. It can be replaced later by explicit metadata from `LocalModel.yaml` or SQLite.

## CLI integration

```bash
local-ai list
local-ai list --all
local-ai inspect qwen3.5:4b
local-ai pull qwen3.5:4b
local-ai rm qwen3.5:4b
```

`local-ai list` now shows capabilities and size.

## API integration

Normalized model metadata is available at:

```http
GET /api/models
```

OpenAI-compatible model listing remains available at:

```http
GET /v1/models
```

The `/v1/models` response includes extra `local_ai_hub` metadata for clients that want capabilities, size, family, and runtime.

## Next roadmap step

Add `LocalModel.yaml` package support so users can define named model presets with system prompts, parameters, RAG collections, and capabilities.
