# Local AI Hub

A fully local, multimodal AI workstation that runs on your own machine. It provides chat, agents, document search, voice, vision, image generation, local memory, CLI tools, LocalModel package presets, and a local API server.

Built for: **NVIDIA GPU 16 GB VRAM · 32 GB RAM · Intel Core i5**.

## Product direction

Local AI Hub is the product name. Runtime/backend names are mentioned only as factual setup or compatibility details.

The project is evolving into a local LLM platform with:

- a Gradio desktop-style UI
- the `local-ai` CLI
- an OpenAI-compatible local API
- a shared runtime abstraction
- a shared model manager
- `LocalModel.yaml` package presets
- optional direct GGUF runtime support
- local RAG, memory, tools, and agent workflows

## Main capabilities

- Chat and coding help with local models
- Model and package switching
- LocalModel package presets
- Document indexing and RAG
- Agent mode with tools
- Team mode with planner, workers, and reviewer
- Voice chat and transcription
- Vision, screen analysis, image generation, and video generation
- Local memory
- Approval-gated file edits
- Read-only email tools
- MCP tool plugins
- QLoRA fine-tuning workflow
- Local API server
- Optional GGUF model discovery and direct runtime path

## Install

Use the setup scripts in `setup/`, or install manually:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Install and start the configured local runtime backend separately, then pull the default chat and embedding models listed in `app/core/config.py`.

## Run the UI

```bash
bash setup/start.sh
```

Open:

```text
http://localhost:7860
```

Manual run:

```bash
python -m app.main
```

## CLI

```bash
local-ai list
local-ai list --all
local-ai packages
local-ai create -f LocalModel.yaml
local-ai inspect qwen3.5:4b
local-ai inspect saree-assistant
local-ai model qwen3.5:4b
local-ai run "Write a Python function to parse CSV files"
local-ai run --model saree-assistant "Draft a customer follow-up"
local-ai chat
local-ai api
local-ai serve
local-ai doctor
```

See `docs/CLI.md`.

## API

Start the API server:

```bash
local-ai api
```

Default local URL:

```text
http://127.0.0.1:11435
```

OpenAI-compatible base URL:

```text
http://127.0.0.1:11435/v1
```

See `docs/API.md`.

## LocalModel packages

A `LocalModel.yaml` package is a named preset over an installed runtime model.

Example:

```yaml
name: saree-assistant
description: Assistant for saree manufacturing, inventory, sales, and design workflows.
base: qwen3.5:4b
system: |
  You are a helpful assistant for saree manufacturing, stock planning,
  sales follow-up, design ideas, and customer communication.
parameters:
  temperature: 0.4
  top_p: 0.9
capabilities:
  - chat
  - code
  - vision
```

Install packages with:

```bash
local-ai create -f LocalModel.yaml
```

Use them anywhere a chat model is accepted:

```bash
local-ai run --model saree-assistant "Write a product description"
```

See `docs/LOCALMODEL.md`.

## Optional GGUF runtime path

Place `.gguf` files in:

```text
data/gguf/
```

List them with:

```bash
AIHUB_RUNTIME=llamacpp local-ai list
```

Run them only after installing the optional runtime dependency described in `docs/LLAMACPP.md`.

## How it learns

Large language models do not update their weights while you chat. This app uses local memory and optional fine-tuning:

- Important facts and behavioral lessons are stored locally.
- Relevant memories are recalled into context on future messages.
- Chat logs can be exported into a QLoRA fine-tuning workflow.
- Fine-tuning can create a custom local model from curated examples.

See `finetune/README.md`.

## Guardrails

- File edits are approval-gated.
- Originals are backed up before approved edits are applied.
- Git work happens in a workspace folder.
- Generated code and shell commands should be reviewed before use.
- Email tools are read-only by design.

## Project layout

```text
app/
  main.py                 Gradio UI
  cli.py                  local-ai CLI
  api/server.py           local API server
  runtime/                runtime abstraction
  models/                 model manager
  model_packages/         LocalModel.yaml support
  chat/                   chat streaming and history
  rag/                    document indexing and retrieval
  media/                  voice, vision, image, video
  services/               research, hooks, mail, scheduler, MCP
finetune/                 QLoRA fine-tuning workflow
data/documents/           files to index
data/models/              LocalModel packages
data/gguf/                optional GGUF model files
data/chatlogs/            chat logs for optional fine-tuning
outputs/                  generated/exported files
setup/                    install and update scripts
docs/                     CLI, API, architecture, runtime, model manager, package docs
tests/                    pytest suite
```

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/CLI.md`
- `docs/API.md`
- `docs/RUNTIME.md`
- `docs/MODEL_MANAGER.md`
- `docs/LOCALMODEL.md`
- `docs/LOCALMODEL_CREATE.md`
- `docs/LLAMACPP.md`
- `ROADMAP.md`
