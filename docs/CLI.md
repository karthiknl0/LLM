# Local AI Hub CLI

The `local-ai` command is the first roadmap milestone toward an Ollama-style local LLM platform.

## Install

From the repository root, after installing the existing requirements:

```bash
pip install -e .
```

This registers the `local-ai` console command.

## Commands

### Show installed chat models

```bash
local-ai list
```

The active model is marked with `*`.

### Show or switch active model

```bash
local-ai model
local-ai model qwen3.5:4b
```

### Run one prompt

```bash
local-ai run "Write a Python function to parse a CSV file"
local-ai run --model qwen3.5:4b "Explain RAG in simple words"
```

Use `--no-stream` to print only the final response.

### Start an interactive terminal chat

```bash
local-ai chat
local-ai chat --model qwen3.5:4b
```

Exit with `/exit`, `/quit`, `Ctrl-C`, or `Ctrl-D`.

### Pull or remove models

```bash
local-ai pull qwen3.5:4b
local-ai rm qwen3.5:4b
```

These commands use Ollama under the hood.

### Health checks

```bash
local-ai status
local-ai doctor
```

Both commands run the existing Local AI Hub checks for Ollama, models, GPU, data, email, and MCP configuration.

### Start the UI server

```bash
local-ai serve
local-ai serve --host 0.0.0.0 --port 7860 --password secret
```

By default, the server binds to `127.0.0.1:7860` unless `AIHUB_HOST` or `AIHUB_PORT` are set.

Use `--browser` to open the browser automatically.

## Current limitations

- The CLI currently wraps the existing Ollama-backed runtime.
- It does not yet expose the roadmap API server.
- It does not yet support `LocalModel.yaml` packages.
- It does not yet abstract multiple runtimes such as llama.cpp, vLLM, or Transformers.

## Next roadmap step

Add an API server with:

```http
GET  /health
GET  /api/tags
POST /api/chat
POST /v1/chat/completions
GET  /v1/models
```

This will make the project usable by OpenAI-compatible clients while keeping the current Gradio UI.
