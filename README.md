# Local AI Hub

Your own fully-local, multimodal AI assistant. No API keys, no subscriptions,
no internet required after setup. Everything runs on your own machine.

Built for: **NVIDIA GPU 16 GB VRAM · 32 GB RAM · Intel Core i5**

## What it can do

| Capability | How | Status on 16 GB GPU |
|---|---|---|
| Chat & coding help | Qwen 3 14B via Ollama | Fast, fully on GPU |
| Agent mode (auto tool use) | Native tool calling: docs, web, Python, images | Fast |
| Run Python for you | Agent writes & executes code in `data/workspace/` | Fast |
| Learn from corrections | Behavioral lessons stored alongside facts | Automatic |
| Deep research / deep answer | Multi-angle search + self-review passes | Slower, better |
| Read your PDFs / Excel / code (RAG) | Local vector DB (ChromaDB) + Ollama embeddings | Fast |
| Understand images | Qwen 2.5-VL 7B vision model | Fast |
| Understand videos | Frame sampling + vision model | Works (samples key frames) |
| Voice chat (speak & listen) | Whisper + Kokoro TTS | Fast, fully local |
| Transcribe audio/video files | Whisper, timestamped | Fast |
| Web research with citations | DuckDuckGo + local LLM | Fast (needs internet) |
| Generate images | Stable Diffusion XL Turbo | ~2–5 s per image |
| Generate videos | LTX-Video | Experimental — short clips, several minutes each |
| Remember you across sessions | Local long-term memory (ChromaDB) | Automatic |
| Self-upgrade | `setup/update.sh` pulls newest models | Run any time |
| Learn from you (weight-level) | QLoRA fine-tuning on your chat logs | See `finetune/README.md` |

## Setup (one time)

### 1. Install Ollama and pull the models

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh
# Windows: download the installer from https://ollama.com/download

ollama pull qwen3:14b          # chat + coding brain (~9 GB)
ollama pull qwen2.5vl:7b       # vision: images & video frames (~6 GB)
ollama pull nomic-embed-text   # embeddings for document search (~275 MB)
```

### 2. Set up Python environment

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# PyTorch with CUDA (check https://pytorch.org for your CUDA version)
pip install torch --index-url https://download.pytorch.org/whl/cu121

pip install -r requirements.txt
```

Or on Linux just run:

```bash
bash setup/install.sh
```

## Run it

```bash
ollama serve                     # if not already running as a service
python -m app.main
```

Open http://localhost:7860 in your browser.

## Using it

- **Agent** — the smartest way to use the hub: one chat where the model
  itself decides when to search your documents, research the web, run
  Python, or generate an image. You'll see *Searching your documents…*
  style notes while it works. Drop data files into `data/workspace/` and
  ask for analysis — the model writes and runs real code instead of
  guessing at numbers (note: that code runs on your machine, with a
  60-second timeout, confined to the workspace folder by convention).
  Tick **Deep answer** to make it review its own draft before replying.
- **Chat** — plain conversation with the local model, no tools.
- **Voice** — record a question with your mic, hear the answer spoken back.
  (Spoken replies need `espeak-ng`: `sudo apt install espeak-ng` on Linux.)
- **Transcribe** — drop in a meeting recording, voice note, or video and
  get a timestamped transcript.
- **Research** — Perplexity-style web answers: your local model searches
  DuckDuckGo, reads the top pages, and replies with `[n]` citations.
  The only feature that uses the internet — no API keys involved, and
  the reasoning still happens on your GPU. Tick **Deep research** for
  multiple search angles and a verification pass against the sources.
- **Documents** — drop PDFs, Excel files, and code into `data/documents/`,
  click *Index documents*, then ask questions about them. Behind the
  scenes, 20 candidate passages are fetched and a local reranker model
  picks the best 5 — noticeably better answers than plain vector search.
- **Vision** — upload an image or video and ask anything about it.
- **Generate Image** — type a prompt, get an image in seconds.
  Saved to `outputs/`.
- **Generate Video** — experimental. Short clips (~3–5 s). The model is
  downloaded on first use (~10 GB) and generation takes several minutes.

## How it "learns"

Large language models don't update their weights while you chat — not even
the frontier ones. What feels like learning is memory: relevant facts placed
into the model's context at the right time. This app does exactly that:

- After each chat turn, a fact worth keeping (your preferences, projects,
  decisions) is extracted and stored locally in ChromaDB. When you
  *correct* the assistant, it also stores a behavioral lesson ("when
  asked about X, do Y") so it stops repeating mistakes.
- On every new message, relevant memories are recalled and given to the
  model, so it remembers you across restarts.
- The **Memory** tab lets you review or wipe everything — it's your data,
  on your disk.

To upgrade the model itself, run `bash setup/update.sh` — open-source models
improve every few months, and pulling a newer one is how your AI gets
permanently smarter.

For true weight-level learning, your chats are logged locally and can be
used to **fine-tune your own model** with QLoRA — it permanently absorbs
your style and becomes `my-ai` in Ollama. Full guide: `finetune/README.md`.

## Honest notes on your hardware

- Qwen 3 14B (4-bit) uses ~10 GB VRAM — fits fully on your GPU and is fast.
- Only one heavy model runs on the GPU at a time. The app loads image/video
  generators on demand and frees them afterwards; Ollama similarly swaps
  models. First request after switching tasks is slower — that's normal.
- Video generation at 16 GB uses CPU offload: expect minutes per clip, not
  seconds. For more serious video work, look at ComfyUI + quantized
  Wan 2.1 / LTX-Video workflows.
- Want a bigger brain? `ollama pull qwen3:32b` runs split across GPU+RAM —
  smarter but noticeably slower.

## Bonus: use your model as a coding agent

Your local model can power an AI pair-programmer in any repo — no code
changes needed, it just talks to Ollama:

```bash
pip install aider-chat
cd your-project
aider --model ollama/qwen3:14b
```

Or install the **Continue** extension in VS Code and point it at Ollama
for local autocomplete and chat inside your editor.

## Bonus: evolve algorithms with your model

`evolve/` contains a ready-to-run OpenEvolve experiment (open-source
AlphaEvolve) pointed at your Ollama server — your local model mutates a
program over generations and an evaluator keeps the correct, faster
versions. See `evolve/README.md`.

## Project layout

```
app/
  main.py       Gradio UI (tabs for each capability)
  config.py     model names & paths — change models here
  agent.py      agent mode: chat with automatic tool use
  chat.py       chat with the local LLM
  rag.py        document indexing & retrieval, with reranking
  research.py   web research with citations, plus deep-research mode
  sandbox.py    Python execution for the agent (data/workspace/)
  vision.py     image & video understanding
  voice.py      voice chat (Whisper + Kokoro TTS) & file transcription
  imagegen.py   Stable Diffusion XL Turbo image generation
  videogen.py   LTX-Video text-to-video (experimental)
finetune/
  export_data.py    build training dataset from your chat logs
  train.py          QLoRA fine-tuning (16 GB GPU)
  merge_and_export.py  merge + import into Ollama as your own model
evolve/           OpenEvolve experiment wired to local Ollama
data/documents/ put your files here, then index them
data/chatlogs/  your conversations (auto-logged, used for fine-tuning)
outputs/        generated images & videos
setup/          install & update scripts
```
