---
name: local-ai-hub
description: Architecture map of the Local AI Hub codebase — which file owns what, the conventions, and recipes for common changes (add a tab, add an agent tool, swap a model). Read this BEFORE editing the app so you can jump straight to the right module instead of reading everything.
---

# Local AI Hub — architecture map

Fully-local multimodal assistant. Gradio web UI + Ollama models. No cloud,
no telemetry. Target hardware: NVIDIA RTX 4060, **8.6 GB VRAM**, 32 GB RAM
(treat 8 GB as the real constraint: only one big model on the GPU at a time).

Run it: `python -m app.main` (needs `ollama serve` running). Opens at
http://localhost:7860. Tests: `.\.venv\Scripts\python.exe -m pytest -q`.

## Hard rules (CI-enforced / convention)

- **Every file < 800 lines.** Split into a new submodule before bloating any file.
- One capability per package under `app/`. The Gradio UI lives ONLY in
  `app/main.py`; all logic lives in its own module.
- Heavy ML models load lazily on first use, released after use where VRAM
  matters. Features degrade gracefully — a missing optional dep or failed
  model load prints a warning, never crashes the app.
- Everything runs locally. No cloud APIs, no telemetry, no API keys.

## Package layout

```
app/
  main.py              — Gradio UI: every tab, CSS, launch block
  core/config.py       — model names, all paths, RAG settings, EDIT_ROOTS
  agent/
    loop.py            — streaming generator for the Agent tab (main entry)
    runner.py          — one-shot tool-calling loop + execution helpers
    modes.py           — MAX_TOOL_ROUNDS, READ_ONLY_TOOLS, PLAN_MODE_PROMPT
    prompt.py          — SYSTEM_PROMPT, skill_hints()
  tools/
    registry.py        — ALL tool JSON schemas (TOOLS list), TOOL_FUNCTIONS
                         dispatch table, TOOL_STATUS labels, MCP merge helpers
    file_ops.py        — list_files, read_file, search_files, propose_edit
    code_exec.py       — run_python, run_command (sandboxed)
    git_ops.py         — git_clone, git_status, git_commit, git_push, git_pull
    browser.py         — verify_in_browser
    screen.py          — look_at_screen
  chat/
    stream.py          — plain chat (no tools) streaming, _log_turn
    history.py         — chat history helpers
  rag/
    index.py           — document indexing (chunking + embedding)
    query.py           — retrieve_context (semantic search)
    readers.py         — file-type readers (PDF, DOCX, TXT, …)
  memory/store.py      — long-term memory + lessons (recall, remember)
  skills/library.py    — self-taught skills (maybe_learn, load/save)
  subagents/team.py    — multi-agent team (planner / workers / reviewer)
  content/
    instructions.py    — standing instructions from data/instructions.md
    coding_profile.py  — CODING_AGENT_PROFILE (appended to system prompt)
    playbooks.py       — authored playbooks (load_playbook, catalog_hint)
    notes.py           — session notes (read_notes, take_note)
  session/
    modelstate.py      — runtime model selection, persisted to data/model.txt
    evals.py           — LLM-as-judge evals
    promptlab.py       — Prompt Helper tab logic
    status.py          — health checks (Status tab)
  services/
    research.py        — web research (search + read + cite)
    mcp.py             — MCP client (was mcp_client.py)
    hooks.py           — session-start hooks (pre_tool, post_reply)
    mail.py            — read-only email (Gmail/IMAP)
    scheduler.py       — scheduled tasks
  media/
    vision.py          — image/video understanding (analyze_media)
    voice.py           — voice in/out (Whisper + Kokoro), transcription
    imagegen.py        — image gen (SDXL Turbo)
    videogen.py        — video gen (LTX)
  personas/manager.py  — persona management
  repo/manager.py      — repo management helpers
  security/
    consistency.py     — self-consistency voting
  commands/handlers.py — slash commands (/model, /vote, …)
```

Data dirs (all gitignored, under `data/`): documents, vectordb, chatlogs,
training, workspace, personas, skills, playbooks, evals, backups. Plus
files: `instructions.md`, `model.txt`, `hooks.json`, `mcp.json`.

## Recipes

### Add a new tab
1. Write the logic in a new module under the appropriate `app/<package>/`.
2. In `app/main.py`: import its entry function, add a `with gr.Tab("Name"):`
   block — `gr.Markdown` intro, inputs, a `variant="primary"` button, output,
   `.click(...)`.
3. Keep `main.py` under 800 lines — the block is just wiring, not logic.

### Add an agent tool
In `app/tools/registry.py`: (1) add the JSON schema to the `TOOLS` list,
(2) map the name to its callable in `TOOL_FUNCTIONS`, (3) add a label in
`TOOL_STATUS`, (4) if read-only (safe in Plan mode) add the name to
`READ_ONLY_TOOLS` in `app/agent/modes.py`.
The function itself lives in the relevant module, not in `registry.py`.

### Change / persist the active model
Model names are in `app/core/config.py` (`CHAT_MODEL`, `VISION_MODEL`,
`EMBED_MODEL`). The *runtime* selection lives in `app/session/modelstate.py`:
`set_model()` writes `data/model.txt`; `_load()` seeds it on startup.

Current lineup: **`qwen3.5:4b`** is the primary brain (`CHAT_MODEL`) and ALSO
the vision model (`VISION_MODEL`) — a 4B multimodal model (3.0 GB) chosen
because it fits 100% in the 8 GB VRAM; the 9B variant spilled ~20% to CPU and
ran ~30x slower. It does clean tool/function calling. `nomic-embed-text` is
embeddings. `installed_models()` only hides embedding models from the chat
picker (must NOT hide the primary). It replaced the gemma4 family, which gave
blank/truncated replies in the agent tool loop (see the workaround code still
in `app/agent/loop.py` and `app/agent/runner.py` — now defensive, harmless).
Agent/chat calls pass `think=False` (qwen3.5 is a reasoning model; thinking on
was ~13x slower with no quality gain here) and the agent loop streams tokens.

### Edit the app's own source as the local agent
`EDIT_ROOTS = [Path.home()]` in `app/core/config.py` covers this repo, so the
agent can `list_files`/`search_files`/`read_file` the source and `propose_edit`
changes — applied only after user approves in the **Approvals** tab. Originals
are backed up to `data/backups/` first.

### Tune the agent's behavior / personality
Edit `SYSTEM_PROMPT` in `app/agent/prompt.py` for tool-use instructions, or
`CODING_AGENT_PROFILE` in `app/content/coding_profile.py` for working habits.
`READ_ONLY_TOOLS` and `PLAN_MODE_PROMPT` live in `app/agent/modes.py`.
User's own always-on rules live in `data/instructions.md` (no restart needed).
