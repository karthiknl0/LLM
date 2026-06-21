# Implementation Status

This document summarizes the roadmap execution status for Local AI Hub.

## Completed

### Product and branding cleanup

- Product-facing language uses `Local AI Hub` and `local LLM platform`.
- Backend names are kept only as factual runtime/setup details.

### CLI

Implemented `local-ai` command with:

```bash
local-ai list
local-ai list --all
local-ai packages
local-ai create -f LocalModel.yaml
local-ai create -f LocalModel.yaml --activate
local-ai inspect <model-or-package>
local-ai model <model-or-package>
local-ai run [--model <model-or-package>] <prompt>
local-ai chat [--model <model-or-package>]
local-ai api
local-ai serve
local-ai status
local-ai doctor
local-ai pull <model>
local-ai rm <model>
```

### API

Implemented local API server with:

```http
GET  /health
GET  /api/models
GET  /api/packages
GET  /api/tags
POST /api/chat
POST /api/generate
GET  /v1/models
POST /v1/chat/completions
```

Package names work anywhere a chat model name is accepted.

### Runtime abstraction

Implemented:

- `app/runtime/base.py`
- `app/runtime/factory.py`
- `app/runtime/ollama_runtime.py`
- `app/runtime/llamacpp_runtime.py`

Runtime selection:

```bash
AIHUB_RUNTIME=ollama
AIHUB_RUNTIME=llamacpp
```

### Model manager

Implemented normalized model metadata and shared operations:

- list installed models
- filter chat-capable models
- infer capabilities
- inspect model metadata
- pull runtime model
- remove runtime model
- check configured defaults

### LocalModel packages

Implemented `LocalModel.yaml` support:

- package loading
- package validation
- package installation through `local-ai create -f`
- package listing
- package inspection
- package use in CLI
- package use in API
- package system prompt merging
- package runtime parameter merging

### llama.cpp / GGUF path

Implemented experimental support:

- `data/gguf/` model directory
- `.gguf` discovery
- listing GGUF models through `AIHUB_RUNTIME=llamacpp local-ai list`
- optional `llama-cpp-python` chat/generate support
- streaming and non-streaming response adapters

Still intentionally not implemented:

- llama.cpp embeddings for RAG
- llama.cpp model download/pull
- llama.cpp model deletion
- advanced chat templates

### Tests and CI

Added focused tests for:

- LocalModel package loading and installation
- LocalModel prompt/parameter merging
- model manager metadata
- CLI parser behavior
- API metadata shape
- runtime factory
- llama.cpp GGUF discovery
- llama.cpp fake-backend chat/generate behavior

CI runs lightweight tests without requiring large ML/UI/media dependencies.

## Documentation

Added or updated:

- `README.md`
- `ROADMAP.md`
- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/CLI.md`
- `docs/RUNTIME.md`
- `docs/MODEL_MANAGER.md`
- `docs/LOCALMODEL.md`
- `docs/LOCALMODEL_CREATE.md`
- `docs/LLAMACPP.md`

## Recommended next optional improvements

These are not required for the current roadmap to be usable:

1. Add llama.cpp embedding support for RAG.
2. Add runtime-specific chat templates.
3. Add API authentication for non-localhost deployments.
4. Add a small UI panel for LocalModel packages.
5. Add release packaging and versioned changelog.
6. Add example package files under `examples/`.
