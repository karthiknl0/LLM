# Local Code

Local Code is a Claude Code-style workflow powered by Local AI Hub's local runtimes.

It does **not** call Claude, Anthropic, or any paid cloud model API. It uses the model selected in Local AI Hub, including LocalModel packages and the optional GGUF runtime path.

## Commands

Ask one coding question:

```bash
local-ai code ask "Explain this project structure"
```

Open an interactive coding session:

```bash
local-ai code chat
```

Create a project instruction file:

```bash
local-ai code init
```

List discovered instruction files:

```bash
local-ai code instructions
```

Index a project for better coding context:

```bash
local-ai code index
local-ai code search "runtime factory"
```

Queue an approval-gated file replacement:

```bash
local-ai code propose --file app/example.py --content-file /tmp/new_example.py --reason "Refactor helper"
local-ai code edits
local-ai code diff <edit-id>
local-ai code apply <edit-id>
local-ai code reject <edit-id>
```

Use a specific local model or package:

```bash
local-ai code --model local-code ask "Review this function"
local-ai code --model saree-assistant chat
```

Use a specific project directory:

```bash
local-ai code --project /path/to/repo ask "Summarize the repo"
```

## Project instructions

Local Code reads project instruction files from the current directory upward.

Supported filenames:

```text
CLAUDE.md
AGENTS.md
.agents.md
.local-ai.md
```

Parent directories are loaded first, then more specific files closer to the project directory.

## Project indexing

`local-ai code index` scans lightweight source and documentation files and stores a compact local JSON index under `data/local_code_index/`.

When you ask a question, Local Code searches the index and injects matching file snippets into the model context. This gives local models more repo awareness without sending code to a cloud API.

## Approval-gated edits

`local-ai code propose` stores proposed complete-file replacements under `data/local_code_edits/`.

Nothing is written to your project until you run:

```bash
local-ai code apply <edit-id>
```

When an edit is applied, the original file is backed up under `data/backups/` first.

## Built-in LocalModel package

The repo includes a `local-code` package preset:

```bash
local-ai model local-code
local-ai code chat
```

## Local-only behavior

Local Code uses:

- the configured Local AI Hub runtime
- the active model or LocalModel package
- local project instruction files
- local project index snippets
- local streaming chat responses

It does not provide paid Claude access and does not bypass Anthropic billing. It gives a similar local workflow using your own model backend.

## Safety notes

- Local Code does not automatically edit files.
- Proposed edits are approval-gated and backed up before application.
- Treat generated commands as suggestions and review them before running.
