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
local-ai code ask <prompt>
local-ai code chat
local-ai code init
local-ai code instructions
local-ai code index
local-ai code search <query>
local-ai code propose --file <path> --content-file <path>
local-ai code edits
local-ai code diff <edit-id>
local-ai code apply <edit-id>
local-ai code reject <edit-id>
local-ai api
local-ai serve
local-ai status
local-ai doctor
local-ai pull <model>
local-ai rm <model>
```

### Local Code workflow

Implemented a Claude Code-style local workflow powered by local models:

- `local-ai code ask` for one-shot coding questions
- `local-ai code chat` for an interactive coding session
- `local-ai code init` to create a `CLAUDE.md`-style instruction file
- `local-ai code instructions` to list project instruction files
- `local-ai code index` and `local-ai code search` for project indexing
- persistent approval queue for proposed file edits
- project instruction discovery for `CLAUDE.md`, `AGENTS.md`, `.agents.md`, and `.local-ai.md`
- no Claude, Anthropic, or paid cloud API calls

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
- runtime chat templates for GGUF/chat completion fallback

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
- shared model/package catalog rows for UI surfaces

### LocalModel packages

Implemented `LocalModel.yaml` support:

- package loading
- package validation
- package installation through `local-ai create -f`
- built-in `local-code` package preset
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
- templates: `plain`, `chatml`, `qwen`, `llama3`, and `mistral`

Still intentionally not implemented:

- llama.cpp embeddings for RAG
- llama.cpp model download/pull
- llama.cpp model deletion

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
- runtime chat templates
- Local Code project instruction discovery and parser behavior
- Local Code project indexing and edit queue behavior
- model/package catalog helpers

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
- `docs/LOCAL_CODE.md`

## Recommended next optional improvements

These are not required for the current roadmap to be usable:

1. Add llama.cpp embedding support for RAG.
2. Add API authentication for non-localhost deployments.
3. Add full Gradio Models tab wiring on top of the tested model catalog helpers.
4. Add release packaging and versioned changelog.
5. Add more example package files under `examples/`.
