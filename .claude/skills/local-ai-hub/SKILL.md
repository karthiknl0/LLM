---
name: local-ai-hub
description: Architecture map of the Local AI Hub codebase — which file owns what, the conventions, and recipes for common changes (add a tab, add an agent tool, swap a model). Read this BEFORE editing the app so you can jump straight to the right module instead of reading everything.
---

# Local AI Hub — architecture map

Fully-local multimodal assistant. Gradio web UI + Ollama models. No cloud,
no telemetry. Target hardware: NVIDIA RTX 4060, **8.6 GB VRAM**, 32 GB RAM
(the code says "16 GB" in places — that was the original assumption; treat
8 GB as the real constraint: only one big model on the GPU at a time).

Run it: `python -m app.main` (needs `ollama serve` running). Opens at
http://localhost:7860. Tests: `.\.venv\Scripts\python.exe -m pytest -q`.

## Hard rules (CI-enforced / convention)

- **Every file < 800 lines.** `agent.py` and `main.py` are both ~735 —
  near the cap. Do NOT bloat them; if a change needs real space there,
  split into a new module instead.
- One capability per module under `app/`. The Gradio UI lives ONLY in
  `app/main.py`; all logic lives in its own module.
- Heavy ML models load lazily on first use, released after use where VRAM
  matters. Features degrade gracefully — a missing optional dep or failed
  model load prints a warning, never crashes the app.
- Everything runs locally. No cloud APIs, no telemetry, no API keys.

## Where things live

| Concern | File |
|---|---|
| Config: model names, all paths, RAG settings | `app/config.py` |
| Active chat model (runtime, persisted to `data/model.txt`) | `app/modelstate.py` |
| Gradio UI — every tab, the CSS, the launch block | `app/main.py` |
| Agent loop + ALL tool schemas + system prompt | `app/agent.py` |
| Coding-agent operating profile (appended to system prompt) | `app/coding_profile.py` |
| Standing instructions (the hub's CLAUDE.md, from `data/instructions.md`) | `app/instructions.py` |
| Plain chat (no tools) streaming | `app/chat.py` |
| Multi-agent team (planner/workers/reviewer) | `app/team.py` |
| File read / list / search / approval-gated edit | `app/fileedit.py` |
| Sandboxed `run_python` / `run_command` | `app/sandbox.py` |
| Git tools (clone, status, commit, push to ai/ branch) | `app/gittools.py` |
| RAG over documents (index + query) | `app/rag.py` |
| Web research (search + read + cite) | `app/research.py` |
| Long-term memory + lessons | `app/memory.py` |
| Vision (image/video understanding) | `app/vision.py` |
| Screen capture + analyze | `app/screen.py` |
| Voice in/out (Whisper + Kokoro) | `app/voice.py` |
| Audio/video transcription | `app/voice.py` / `app/vision.py` |
| Image gen (SDXL Turbo) / Video gen (LTX) | `app/imagegen.py` / `app/videogen.py` |
| Self-taught skills | `app/skills.py` |
| Authored playbooks | `app/playbooks.py` |
| Evals (LLM-as-judge) | `app/evals.py` |
| Personas | `app/personas.py` |
| Slash commands (e.g. /model, /vote) | `app/commands.py` |
| Self-consistency voting | `app/consistency.py` |
| Read-only email (Gmail/IMAP) | `app/mail.py` |
| MCP client | `app/mcp_client.py` |
| Browser verify | `app/browser.py` |
| Health checks (Status tab) | `app/status.py` |
| Prompt improver (Prompt Helper tab) | `app/promptlab.py` |
| Notes (survive context compaction) | `app/notes.py` |
| Session-start hook | `app/hooks.py` |

Data dirs (all gitignored, under `data/`): documents, vectordb, chatlogs,
training, workspace, personas, skills, playbooks, evals, backups. Plus
files: `instructions.md`, `model.txt`, `hooks.json`, `mcp.json`.

## Recipes

### Add a new tab
1. Write the logic in a new `app/<feature>.py` (one capability per module).
2. In `app/main.py`: import its entry function, add a `with gr.Tab("Name"):`
   block following the existing pattern (a `gr.Markdown` intro, inputs, a
   `variant="primary"` button, an output, and a `.click(...)`).
3. Keep `main.py` under 800 lines — the block is just wiring, not logic.

### Add an agent tool
In `app/agent.py`: (1) add the JSON schema to the `TOOLS` list, (2) map the
name to its function in `TOOL_FUNCTIONS`, (3) add a label in `TOOL_STATUS`,
(4) if it's read-only (safe in Plan mode) add the name to `READ_ONLY_TOOLS`.
The function itself lives in the relevant module, not in `agent.py`.

### Change / persist the active model
Model names are in `app/config.py` (`CHAT_MODEL`, `VISION_MODEL`,
`EMBED_MODEL`). The *runtime* selection lives in `app/modelstate.py`:
`set_model()` writes `data/model.txt`; `_load()` seeds it on startup, so the
dropdown choice survives restarts.

Current lineup: **`gemma4:26b`** is the primary brain (`CHAT_MODEL`) and ALSO
the vision model (`VISION_MODEL`) — it's a multimodal MoE that's smart and
fast-once-warm. `qwen3:8b` is a fast fully-in-VRAM fallback. `nomic-embed-text`
is embeddings. Because the vision model is now a general chat model,
`installed_models()` only hides embedding models from the chat picker (it must
NOT hide the primary). NB: `gemma4:e4b`'s image input via Ollama is broken;
only `26b` does vision correctly.

### Edit the app's own source as the local agent
`EDIT_ROOTS = [Path.home()]` in config covers this repo (it's under the home
dir), so the agent can `list_files`/`search_files`/`read_file` the source and
`propose_edit` changes — which apply only after the user approves them in the
**Approvals** tab. Original files are backed up to `data/backups/` first.

### Tune the agent's behavior / personality
Edit the `SYSTEM_PROMPT` in `app/agent.py` for tool-use instructions, or
`CODING_AGENT_PROFILE` in `app/coding_profile.py` for working habits. User's
own always-on rules live in `data/instructions.md` (no restart needed).
