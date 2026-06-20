# Architecture

Local AI Hub is organized as a local LLM platform with a UI, CLI, API server, runtime abstraction, model manager, package presets, and local assistant features.

## High-level flow

```text
User
  ├─ Gradio UI
  ├─ local-ai CLI
  └─ Local API server
        ↓
Session state and package resolution
        ↓
Model manager
        ↓
Runtime abstraction
        ↓
Configured local backend
```

## Main layers

### UI

`app/main.py` builds the Gradio interface and wires the user-facing tabs.

### CLI

`app/cli.py` provides the `local-ai` command.

Important commands:

```bash
local-ai list
local-ai packages
local-ai inspect <model-or-package>
local-ai run --model <model-or-package> "prompt"
local-ai chat --model <model-or-package>
local-ai api
local-ai serve
```

### API

`app/api/server.py` exposes local API routes and OpenAI-compatible chat routes.

Important endpoints:

```http
GET  /health
GET  /api/models
GET  /api/packages
POST /api/chat
POST /api/generate
GET  /v1/models
POST /v1/chat/completions
```

### LocalModel packages

`app/model_packages/` loads `LocalModel.yaml` package presets. Packages map a name to a base model plus system prompt, parameters, capabilities, and future RAG/tool defaults.

### Model manager

`app/models/` normalizes model metadata and centralizes model listing, filtering, capability inference, pull, and remove operations.

### Runtime abstraction

`app/runtime/` owns backend selection and model operations.

Current files:

```text
app/runtime/base.py
app/runtime/factory.py
app/runtime/ollama_runtime.py
app/runtime/llamacpp_runtime.py
```

`OllamaRuntime` is the default production backend. `LlamaCppRuntime` can discover `.gguf` files from `data/gguf/`, but inference is not implemented yet.

### GGUF model discovery

`data/gguf/` is reserved for direct local GGUF model files.

Example:

```text
data/gguf/demo.gguf
data/gguf/qwen/qwen-test.gguf
```

With `AIHUB_RUNTIME=llamacpp`, these appear as runtime models:

```bash
AIHUB_RUNTIME=llamacpp local-ai list
```

Chat/generate/embed are still disabled for this backend until inference is implemented.

### RAG

`app/rag/` indexes documents into ChromaDB and retrieves relevant chunks for local answers.

### Agents and tools

Agent, research, file, browser, mail, MCP, memory, and media features sit above the same model/runtime layers.

## Runtime selection

The runtime is selected through:

```bash
AIHUB_RUNTIME=ollama
```

Reserved/discovery-only value:

```bash
AIHUB_RUNTIME=llamacpp
```

## Design rules

1. UI, CLI, API, RAG, and agents should not call backend clients directly.
2. New model backends should implement the runtime interface.
3. Model listing and capability decisions should go through the model manager.
4. Named presets should go through LocalModel packages.
5. Product-facing language should use Local AI Hub / local LLM platform; backend names should be factual runtime details only.

## Next architecture step

Implement non-streaming `generate` in `LlamaCppRuntime`. The safest order is:

1. Add optional dependency docs for the chosen backend library.
2. Add a loader for one `.gguf` file by model name.
3. Implement non-streaming `generate`.
4. Implement non-streaming `chat` by formatting messages.
5. Add streaming.
6. Add embedding support only if a compatible embedding model is configured.
7. Add tests with fake objects so CI does not need a real model file.
