# Fine-tune your own model (QLoRA)

This is real weight-level learning: the model permanently absorbs your
style and knowledge, instead of just recalling memories. Everything runs
on your 16 GB GPU. Budget an afternoon the first time.

## How it works

Your chats in the app are logged automatically to `data/chatlogs/`.
Those conversations become training data. QLoRA freezes the base model
in 4-bit and trains a small "adapter" on top — that's what makes 7B
fine-tuning possible on 16 GB VRAM. The adapter is then merged back in
and imported into Ollama as your own named model.

## Prerequisites

```bash
source .venv/bin/activate
pip install -r finetune/requirements-finetune.txt
```

Note: `bitsandbytes` needs Linux or WSL2 on Windows.

## The 4 steps

```bash
# 1. Collect data — just use the app. Aim for 100+ good chat turns.
#    Optionally add hand-written examples in data/training/custom.jsonl:
#    {"user": "question", "assistant": "ideal answer"}

# (optional) Learn from a codebase: turn a project into training data
#    that teaches the model THIS code's style and patterns.
python -m finetune.code_to_dataset /path/to/your/project

# 2. Build the dataset from your logs (+ any code data above)
python -m finetune.export_data

# 3. Train (roughly 1-3 hours on your GPU)
python -m finetune.train

# 4. Merge and import into Ollama as 'my-ai'
python -m finetune.merge_and_export
```

Then point the app at your model: in `app/config.py` set

```python
CHAT_MODEL = "my-ai"
```

Restart the app — you're now chatting with a model trained on you.

## Tips for good results

- **Quality beats quantity.** 200 great examples outperform 2,000 sloppy
  ones. Delete bad conversations from `data/chatlogs/` before exporting.
- **Curate.** If the assistant gave a weak answer in a logged chat, either
  delete that line or rewrite the answer the way you wish it had responded —
  the model learns to imitate whatever you feed it.
- **Don't expect new facts.** Fine-tuning teaches style, tone, and patterns.
  For factual knowledge about your documents, the RAG tab is the right tool.
- **Retrain occasionally**, not constantly. Every month or two, after your
  logs have grown, repeat steps 2-4. Each run starts fresh from the base
  model, so there's no compounding drift.
- If you run out of VRAM, lower `MAX_SEQ_LENGTH` to 512 or `LORA_RANK` to 8
  in `finetune/config.py`.
