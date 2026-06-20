# Roadmap: From Local AI Hub to Ollama-Style LLM Platform

This repository already contains a strong local AI assistant built on top of Ollama, Gradio, RAG, tools, memory, voice, vision, image generation, and fine-tuning workflows.

The next product goal is to evolve it into a standalone local LLM platform with an Ollama-like developer experience while keeping the current Local AI Hub as the rich UI layer.

## Current state

The project currently provides:

- Local chat through Ollama-backed models.
- Runtime model switching from the UI and slash commands.
- Document indexing and RAG using ChromaDB and Ollama embeddings.
- Agent, team, research, browser verification, file tools, and memory features.
- Voice, vision, image generation, video generation, screen analysis, and transcription.
- QLoRA fine-tuning workflow that can create a custom Ollama model from chat logs.

This is currently best described as:

```text
Ollama + Local AI Hub UI + RAG + Agent Tools + Fine-tuning Workflow
```

The target platform should become:

```text
Local model runtime wrapper + CLI + API server + model manager + UI + agent layer
```

## Product goals

1. Provide an easy local LLM command-line experience.
2. Expose stable local APIs for apps, agents, and integrations.
3. Manage models cleanly from one place.
4. Keep compatibility with Ollama where useful.
5. Keep the app fully local-first and privacy-preserving.
6. Preserve the existing Gradio hub as the default graphical interface.

## Phase 1 — CLI foundation

Create a first-party CLI entrypoint named `local-ai`.

Target commands:

```bash
local-ai chat
local-ai run <model>
local-ai serve
local-ai list
local-ai pull <model>
local-ai rm <model>
local-ai status
local-ai doctor
```

Implementation notes:

- Use Python `argparse` or `typer`.
- Reuse existing modules such as `app.session.modelstate`, `app.chat.stream`, and `app.session.status`.
- Keep the CLI thin at first; it can call Ollama underneath.
- Add a `pyproject.toml` console script entrypoint.

Acceptance criteria:

- `local-ai chat` opens an interactive terminal chat.
- `local-ai list` shows installed chat-capable models.
- `local-ai run qwen3.5:4b` sends one prompt to the selected model.
- `local-ai doctor` checks Ollama, models, Python dependencies, GPU availability, and data directories.

## Phase 2 — Local API server

Add a backend API server that can run without the Gradio UI.

Target endpoints:

```http
GET  /health
GET  /api/tags
POST /api/chat
POST /api/generate
POST /v1/chat/completions
GET  /v1/models
```

Implementation notes:

- Use FastAPI or another lightweight Python web framework.
- Stream responses using server-sent events or chunked transfer.
- Keep an Ollama-compatible `/api/chat` route.
- Add an OpenAI-compatible `/v1/chat/completions` route for external tools.
- Keep API and UI independent so the CLI can start either one.

Acceptance criteria:

- Existing local models can be used from `curl`.
- API responses support streaming.
- OpenAI-compatible clients can point to `http://localhost:<port>/v1`.
- The Gradio UI can optionally use this API instead of calling model functions directly.

## Phase 3 — Model manager

Build a local model management layer.

Target features:

- List installed models.
- Pull models through Ollama.
- Remove models.
- Show model size, family, modified time, and capabilities.
- Store app-specific metadata in SQLite or JSON.
- Mark models as chat, embedding, vision, coding, or reasoning models.

Implementation notes:

- Start by wrapping `ollama list`, `ollama pull`, and `ollama rm` through the Python Ollama client or subprocess calls.
- Later support non-Ollama runtimes such as `llama.cpp`, `vLLM`, or direct `transformers` pipelines.

Acceptance criteria:

- UI, CLI, and API all read from the same model registry.
- Embedding-only models are hidden from chat dropdowns.
- Missing default models are reported with exact install commands.

## Phase 4 — Model package file

Add a project-level model definition format similar in spirit to Ollama's `Modelfile`.

Possible filename:

```text
LocalModel.yaml
```

Example:

```yaml
name: saree-assistant
base: qwen3.5:4b
system: |
  You are a helpful assistant for saree manufacturing, inventory, sales, and design workflows.
parameters:
  temperature: 0.4
  top_p: 0.9
rag:
  collections:
    - documents
capabilities:
  - chat
  - code
  - vision
```

Target commands:

```bash
local-ai create -f LocalModel.yaml
local-ai run saree-assistant
```

Acceptance criteria:

- A model package can define system prompts, parameters, tools, and RAG defaults.
- Packages can be listed and selected like regular models.
- The current persona system can be mapped into this format over time.

## Phase 5 — Runtime abstraction

Introduce a runtime interface so the platform is not permanently tied to Ollama.

Suggested interface:

```python
class LLMRuntime:
    def list_models(self): ...
    def pull_model(self, name: str): ...
    def chat(self, model: str, messages: list[dict], stream: bool): ...
    def embed(self, model: str, texts: list[str]): ...
```

Initial runtimes:

- `OllamaRuntime`

Future runtimes:

- `LlamaCppRuntime`
- `VLLMRuntime`
- `TransformersRuntime`

Acceptance criteria:

- Chat, RAG, agent tools, and API call the runtime interface instead of importing `ollama` directly.
- Ollama remains the default runtime.
- Adding a new runtime does not require rewriting the UI.

## Phase 6 — Developer polish

Add the pieces needed for a more serious open-source/developer product.

Tasks:

- Add API docs.
- Add CLI docs.
- Add architecture docs.
- Add smoke tests for CLI and API.
- Add GitHub Actions checks for linting and tests.
- Add example `curl` commands.
- Add example OpenAI SDK usage against the local API.
- Add screenshots or a short demo GIF.

Acceptance criteria:

- A new user can install, run, chat, call the API, and index documents using only the README.
- CI catches broken imports and core command failures.
- API and CLI behavior is documented and versioned.

## Suggested implementation order

1. Add `pyproject.toml` with `local-ai` console script.
2. Add `app/cli.py` with `chat`, `list`, `status`, and `doctor`.
3. Add `app/api/server.py` with `/health`, `/api/chat`, and `/v1/chat/completions`.
4. Refactor direct Ollama calls behind `app/runtime/ollama_runtime.py`.
5. Add model manager functions shared by UI, CLI, and API.
6. Add `LocalModel.yaml` package support.
7. Add tests and documentation.

## Near-term MVP

The smallest useful Ollama-style milestone is:

```bash
local-ai list
local-ai run qwen3.5:4b "Write a Python function to parse CSV files"
local-ai serve
curl http://localhost:11435/v1/chat/completions
```

Once this works, the repository becomes both:

- A polished local AI assistant app.
- A reusable local LLM platform that other tools can call.

## Notes

Do not remove Ollama integration early. The fastest path is to wrap Ollama first, stabilize the platform APIs, and only then add alternate runtimes.

The current project already has many advanced assistant features. The main missing layer is productization around CLI, API compatibility, model management, and runtime abstraction.
