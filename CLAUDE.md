# Project conventions

## Code style rules

- **Keep every file under 800 lines.** When a file approaches the limit,
  split it into focused modules (e.g. `rag.py` → `rag_index.py` +
  `rag_query.py`) instead of letting it grow. This keeps debugging easy.
- One capability per module under `app/` (chat, rag, vision, voice, ...).
  The Gradio UI lives only in `app/main.py`; logic lives in the modules.
- Heavy ML models load lazily on first use and are released after use
  where VRAM matters — only one big model on the GPU at a time.
- Features must degrade gracefully: a missing optional dependency or a
  failed model load should print a warning, never crash the app.
- Everything must run fully locally — no cloud APIs, no telemetry.

## Coding principles (Karpathy-inspired)

- **Think before coding.** State assumptions explicitly; when a request
  is ambiguous, present the interpretations rather than picking one
  silently; push back when a simpler approach exists.
- **Simplicity first.** Minimum code that solves the problem — no
  speculative features, no abstractions for single-use code. If 200
  lines could be 50, write 50.
- **Surgical changes.** Touch only what the task requires; match the
  existing style; don't "improve" adjacent code. Clean up orphans your
  change created, leave pre-existing dead code alone (mention it).
- **Goal-driven execution.** Define how success will be verified before
  starting; run the code (or tests) and show it working before calling
  a task done.

## Project overview

Local AI Hub: a fully-local multimodal assistant (chat, RAG over
documents, vision, voice, image/video generation, long-term memory,
QLoRA fine-tuning) targeting a desktop with a 16 GB NVIDIA GPU and
32 GB RAM. Models are served by Ollama; generation models come from
Hugging Face. Configuration is centralized in `app/config.py` and
`finetune/config.py`.

Run the app: `python -m app.main` (requires `ollama serve` running).
