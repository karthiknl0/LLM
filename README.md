# Local AI Hub

Your own fully-local, multimodal AI assistant. No API keys, no subscriptions,
no internet required after setup. Everything runs on your own machine.

Built for: **NVIDIA GPU 16 GB VRAM · 32 GB RAM · Intel Core i5**

## What it can do

| Capability | How | Status on 16 GB GPU |
|---|---|---|
| Chat & coding help | Qwen 3 14B via Ollama | Fast, fully on GPU |
| Read your PDFs / Excel / code (RAG) | Local vector DB (ChromaDB) + Ollama embeddings | Fast |
| Understand images | Qwen 2.5-VL 7B vision model | Fast |
| Understand videos | Frame sampling + vision model | Works (samples key frames) |
| Generate images | Stable Diffusion XL Turbo | ~2–5 s per image |
| Generate videos | LTX-Video | Experimental — short clips, several minutes each |

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

- **Chat** — talk to your local model. It never leaves your machine.
- **Documents** — drop PDFs, Excel files, and code into `data/documents/`,
  click *Index documents*, then ask questions about them.
- **Vision** — upload an image or video and ask anything about it.
- **Generate Image** — type a prompt, get an image in seconds.
  Saved to `outputs/`.
- **Generate Video** — experimental. Short clips (~3–5 s). The model is
  downloaded on first use (~10 GB) and generation takes several minutes.

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

## Project layout

```
app/
  main.py       Gradio UI (tabs for each capability)
  config.py     model names & paths — change models here
  chat.py       chat with the local LLM
  rag.py        document indexing & retrieval (PDF, Excel, CSV, code)
  vision.py     image & video understanding
  imagegen.py   Stable Diffusion XL Turbo image generation
  videogen.py   LTX-Video text-to-video (experimental)
data/documents/ put your files here, then index them
outputs/        generated images & videos
setup/          install script
```
