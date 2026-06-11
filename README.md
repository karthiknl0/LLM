# Local AI Hub

Your own fully-local, multimodal AI assistant. No API keys, no subscriptions,
no internet required after setup. Everything runs on your own machine.

Built for: **NVIDIA GPU 16 GB VRAM · 32 GB RAM · Intel Core i5**

## What it can do

| Capability | How | Status on 16 GB GPU |
|---|---|---|
| Chat & coding help | Qwen 3 14B via Ollama | Fast, fully on GPU |
| Agent mode (auto tool use) | Native tool calling: docs, web, Python, images | Fast |
| Team mode (multi-agent) | Planner → tool-using workers → reviewer | Slower, for big tasks |
| Run Python for you | Agent writes & executes code in `data/workspace/` | Fast |
| Learn from corrections | Behavioral lessons stored alongside facts | Automatic |
| Teach itself skills | Reusable functions saved from solved tasks | Automatic |
| Deep research / deep answer | Multi-angle search + self-review passes | Slower, better |
| Read your PDFs / Excel / Word / PowerPoint / code (RAG) | Local vector DB (ChromaDB) + Ollama embeddings | Fast |
| Chat with any GitHub repo | Shallow clone + the same RAG pipeline | Fast |
| Edit, build & test code | Clone a repo, edit, run its tests/build, fix failures | Supervised |
| Edit your own files (approval-gated) | Proposes diffs; you approve in the Approvals tab; originals backed up | Supervised |
| Edit & push code to GitHub | Guarded git tools — ai/* branches only, you merge via PR | Supervised |
| Verify web pages in a browser | Headless Chromium + vision model + console errors | Fast |
| Plug-in tools via MCP | Any Model Context Protocol server (data/mcp.json) | Depends on server |
| Task scratchpad | Agent takes notes that survive context compaction | Automatic |
| Playbook library | Authored workflows loaded on demand (data/playbooks/) | Automatic |
| Prompt evals | Graded test sets + LLM-as-judge (Evals tab) | On demand |
| Prompt helper | Rewrites a rough prompt using prompt-eng techniques | On demand |
| Slash commands | /help /status /memory /index … in Chat and Agent | Instant |
| Scheduled loops | /loop <min> <prompt> — recurring agent runs with logs | Background |
| Understand images | Qwen 2.5-VL 7B vision model | Fast |
| Understand videos | Frame sampling + vision model | Works (samples key frames) |
| Look at your screen | Screenshot + vision model | Fast, stays on your machine |
| Voice chat (speak & listen) | Whisper + Kokoro TTS | Fast, fully local |
| Transcribe audio/video files | Whisper, timestamped | Fast |
| Web research with citations | DuckDuckGo + local LLM | Fast (needs internet) |
| Generate images | Stable Diffusion XL Turbo | ~2–5 s per image |
| Generate videos | LTX-Video | Experimental — short clips, several minutes each |
| Remember you across sessions | Local long-term memory (ChromaDB) | Automatic |
| Self-upgrade | `setup/update.sh` pulls newest models | Run any time |
| Learn from you (weight-level) | QLoRA fine-tuning on your chat logs | See `finetune/README.md` |

## Setup (one time)

### One-line install

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/karthiknl0/LLM/main/setup/bootstrap.ps1 | iex
```

**Linux / WSL2:**

```bash
curl -fsSL https://raw.githubusercontent.com/karthiknl0/LLM/main/setup/bootstrap.sh | bash
```

Either clones the repo to `~/local-ai-hub` (or `%USERPROFILE%\local-ai-hub`)
and runs the full setup — Ollama, the three models (~15 GB download),
Python environment, and all dependencies. When it finishes:

```powershell
# Windows
cd $env:USERPROFILE\local-ai-hub; powershell -ExecutionPolicy Bypass -File setup\start.ps1
```

```bash
# Linux / WSL2
cd ~/local-ai-hub && bash setup/start.sh
```

Windows notes: needs git and Python installed (`winget install Git.Git
Python.Python.3.12`). Spoken replies want espeak-ng (installer at
github.com/espeak-ng/espeak-ng/releases) — everything else works without
it. QLoRA fine-tuning (`finetune/`) is the one feature that needs WSL2.

Prefer to see what you're running first? The scripts are in `setup/`,
and the manual steps below do the same thing.

### Manual setup

#### 1. Install Ollama and pull the models

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh
# Windows: download the installer from https://ollama.com/download

ollama pull qwen3:14b          # chat + coding brain (~9 GB)
ollama pull qwen2.5vl:7b       # vision: images & video frames (~6 GB)
ollama pull nomic-embed-text   # embeddings for document search (~275 MB)
```

#### 2. Set up Python environment

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
bash setup/start.sh              # starts Ollama too, if needed
```

Open http://localhost:7860 in your browser. (Or manually: `ollama serve`
then `python -m app.main`.)

**From your phone:** `bash setup/start.sh --lan` makes the hub reachable
on your home WiFi at `http://<your-pc-ip>:7860`. Set a password first if
others use your network: `AIHUB_PASSWORD=secret bash setup/start.sh --lan`
(login username is `me`). Your AI in your pocket — still running entirely
on your desktop.

If something doesn't work, the **Status** tab diagnoses it: Ollama not
running, models not pulled, GPU not visible, low disk — with the exact
command to fix each.

## Using it

Type `/help` in the Chat or Agent box for slash commands — instant
actions like `/status`, `/memory`, `/index`, `/note <text>`, and
`/approvals` without leaving the conversation. Recurring work: `/loop 30
research X and note anything new` re-runs a prompt (with full agent
tools) every 30 minutes and logs results to `data/loops/` — `/loops`
lists them, `/stoploop <id>` stops one. Loops live while the app runs.
When a chat gets long or changes topic, `/compact` summarizes it — the
summary stays visible and older turns leave the model’s context (the
same also happens automatically past ~12k characters).

- **Agent** — the smartest way to use the hub: one chat where the model
  itself decides when to search your documents, research the web, run
  Python, or generate an image. You'll see *Searching your documents…*
  style notes while it works. Attach images or videos with 📎 and it
  consults the vision model; attach CSVs or other data files and they
  land in `data/workspace/` where the model writes and runs real code
  instead of guessing at numbers (note: that code runs on your machine,
  with a 60-second timeout, confined to the workspace folder by
  convention). Tick **Deep answer** to make it review its own draft
  before replying. When it builds or changes a web page, it verifies
  the result in a headless browser — screenshot checked by the vision
  model, console errors included — before telling you it's done.
- **Team** — multi-agent mode for big jobs: a planner agent splits your
  task into subtasks, worker agents execute each one with the full
  toolset, and a reviewer agent merges the results into one answer.
  The roles run sequentially on your one GPU (parallel agent frameworks
  like CrewAI assume cloud APIs) — you watch the plan execute live.
- **Chat** — plain conversation with the local model, no tools. A
  persona dropdown switches in specialist system prompts (Code Reviewer,
  Writing Editor, Socratic Tutor, …) — edit them or add your own as
  `.md` files in `data/personas/` (filename = name, content = prompt).
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
  You can also paste a GitHub URL to clone and index a whole codebase,
  then ask questions about it ("how does auth work in this repo?") —
  cloning is the only network step, the analysis stays local.
- **Vision** — upload an image or video and ask anything about it.
- **Screen** — one click captures your screen and the vision model
  answers questions about it ("what does this error mean?"). Also
  available in the Agent: just say "look at my screen and …".
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
- When the agent solves a task with code, the reusable part is saved as
  a named function in `data/skills/` (the **Skills** tab lists them).
  Next time a similar task comes up, the agent is told to import the
  saved skill instead of rewriting it — a personal standard library
  built from your actual problems.
- The **Memory** tab lets you review or wipe everything — it's your data,
  on your disk.

To upgrade the model itself, run `bash setup/update.sh` — open-source models
improve every few months, and pulling a newer one is how your AI gets
permanently smarter.

For true weight-level learning, your chats are logged locally and can be
used to **fine-tune your own model** with QLoRA — it permanently absorbs
your style and becomes `my-ai` in Ollama. Full guide: `finetune/README.md`.

## Honest notes on your hardware

- Long conversations are compacted automatically: when a chat outgrows
  the context window, older turns are summarized and recent turns kept
  word-for-word — the model stops silently forgetting the start. During
  long tasks the agent also keeps a scratchpad (`data/workspace/NOTES.md`)
  whose recent notes are always in view, so working state survives
  compaction.
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

## Playbooks: teach the agent your workflows

`data/playbooks/` holds authored step-by-step workflows as `.md` files
(frontmatter + a When-to-use / Workflow / Verification body). The agent
always sees the cheap one-line descriptions, and loads a playbook's full
text only when a task matches — progressive disclosure, so many
playbooks cost almost no context until used. Write your own for
recurring work ("deploy my site", "review a PR"), or drop in a published
library that follows the same format (e.g. an authorized
defensive-security playbook set). Two examples are seeded on first run.

This differs from the **Skills** tab (functions the agent writes itself)
and **personas** (whole-chat system prompts): playbooks are reference
procedures you author once and the agent follows on demand.

## Editing your files: the approval gate

The agent can read files anywhere in your home folder and *propose*
edits to them — but **nothing is written until you approve the diff in
the Approvals tab**, and the original is backed up to `data/backups/`
first. This is the same architecture Claude Code uses: broad read
access, human approval on every write. Ask things like *"fix the typo
in C:/Users/you/notes/draft.md"* — the agent queues a diff and tells
you it's waiting for approval. Allowed folders are `EDIT_ROOTS` in
`app/config.py` (default: your home directory) — narrow it if you wish.

## MCP: plug-in tools for the agent

The agent speaks [Model Context Protocol](https://modelcontextprotocol.io) —
the same plug-in standard Claude uses. Hundreds of community servers
exist (filesystem, SQLite/Postgres, Home Assistant, browsers, Slack, …).
Add them in `data/mcp.json` (Claude Desktop's config shape):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/you/notes"]
    }
  }
}
```

Restart the app; each server's tools appear to the agent automatically
(named `mcp_<server>_<tool>`), and the Status tab shows what connected.
Servers run as local subprocesses. Only add servers you trust — each one
is code running on your machine with the powers you give it, and the
agent will be able to call everything it offers.

Starter examples (filesystem, SQLite) are in `setup/mcp.example.json`;
browse [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
for the full catalog. Two rules of thumb: prefer local-first servers
that need no API keys, and keep the count low — every connected tool
definition eats context, and a 14B model chooses tools best from a
short, distinct list. One or two servers that match your real workflow
beat ten installed "just in case".

## Agent + GitHub (guarded)

The agent can clone a repo, edit it, build and test it (`run_command`
in the repo folder — `pytest`, `npm test`, `npm run build`, …, with a
10-minute timeout), then commit and push — with guardrails enforced in
code, not prompts:

- work happens only in `data/workspace/repos/`
- commits only land on branches named `ai/<something>`
- pushing `main`/`master` is physically impossible; no force-push exists
- **you merge via pull request** — the agent proposes, you review

Try: *"clone https://github.com/you/yourrepo, add a script that does X,
commit it, and push"*. The push uses your normal git credentials, or set
a fine-grained token first for tighter scoping (recommended — limit it
to chosen repos, Contents: read & write):

```powershell
$env:AIHUB_GITHUB_TOKEN = "github_pat_..."   # Windows
```

```bash
export AIHUB_GITHUB_TOKEN="github_pat_..."   # Linux
```

Worst case from a confused model is a messy `ai/*` branch you delete —
never a broken `main`.

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
  team.py       multi-agent team: planner → workers → reviewer
  chat.py       chat with the local LLM
  history.py    long-conversation compaction (summarize older turns)
  personas.py   switchable specialist prompts (data/personas/*.md)
  rag.py        document indexing & retrieval, with reranking
  repo.py       clone GitHub repos into the document index
  gittools.py   guarded git tools: agent commits to ai/* branches
  mcp_client.py MCP plug-in tools for the agent (data/mcp.json)
  notes.py      agent scratchpad for long tasks (survives compaction)
  playbooks.py  authored workflows, loaded on demand (data/playbooks/)
  evals.py      local prompt evaluations (Evals tab, data/evals/)
  fileedit.py   approval-gated edits to your own files (Approvals tab)
  promptlab.py  prompt improver (Prompt Helper tab)
  research.py   web research with citations, plus deep-research mode
  browser.py    headless-browser verification of web pages
  sandbox.py    Python execution for the agent (data/workspace/)
  skills.py     self-built skill library (data/skills/)
  screen.py     screen capture + vision analysis
  status.py     system health checks (Status tab)
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
