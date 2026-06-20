# Local AI Hub CLI

The `local-ai` command is the first roadmap milestone toward an Ollama-style local LLM platform.

## Install

From the repository root, after installing the existing requirements:

```bash
pip install -e .
```

This registers the `local-ai` console command.

## Commands

### Show installed models

```bash
local-ai list
local-ai list --all
```

The active model is marked with `*`. The list shows inferred capabilities and size. By default, embedding-only models are hidden; use `--all` to include them.

### Inspect one model

```bash
local-ai inspect qwen3.5:4b
```

Shows normalized metadata such as runtime, capabilities, size, family, and modified time.

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

These commands go through the shared model manager and configured runtime.

### Health checks

```bash
local-ai status
local-ai doctor
```

Both commands run the existing Local AI Hub checks for runtime, models, GPU, data, email, and MCP configuration.

### Start the UI server

```bash
local-ai serve
local-ai serve --host 0.0.0.0 --port 7860 --password secret
```

By default, the UI server binds to `127.0.0.1:7860` unless `AIHUB_HOST` or `AIHUB_PORT` are set.

Use `--browser` to open the browser automatically.

### Start the API server

```bash
local-ai api
local-ai api --host 0.0.0.0 --port 11435
```

By default, the API server binds to `127.0.0.1:11435` unless `AIHUB_API_HOST` or `AIHUB_API_PORT` are set.

The OpenAI-compatible base URL is:

```text
http://127.0.0.1:11435/v1
```

See `docs/API.md` for curl and SDK examples.

## Current limitations

- The CLI and API currently wrap the existing Ollama-backed runtime.
- Model capabilities are inferred from names and runtime metadata until `LocalModel.yaml` exists.
- API auth is not implemented yet; keep the API bound to `127.0.0.1` unless you trust your network.
- Token usage values in OpenAI-compatible responses are placeholders for now.
- It does not yet support `LocalModel.yaml` packages.
- It does not yet provide alternate runtimes such as llama.cpp, vLLM, or Transformers.

## Next roadmap step

Add `LocalModel.yaml` package support for named presets with system prompts, parameters, RAG defaults, and explicit capabilities.
