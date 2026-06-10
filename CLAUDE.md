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

## Project overview

Local AI Hub: a fully-local multimodal assistant (chat, RAG over
documents, vision, voice, image/video generation, long-term memory,
QLoRA fine-tuning) targeting a desktop with a 16 GB NVIDIA GPU and
32 GB RAM. Models are served by Ollama; generation models come from
Hugging Face. Configuration is centralized in `app/config.py` and
`finetune/config.py`.

Run the app: `python -m app.main` (requires `ollama serve` running).
