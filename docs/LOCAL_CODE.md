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

Use a specific local model or package:

```bash
local-ai code --model qwen3.5:4b ask "Review this function"
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

## Local-only behavior

Local Code uses:

- the configured Local AI Hub runtime
- the active model or LocalModel package
- local project instruction files
- local streaming chat responses

It does not provide paid Claude access and does not bypass Anthropic billing. It gives a similar local workflow using your own model backend.

## Safety notes

- Local Code does not automatically edit files in this first version.
- It can explain code, plan changes, review snippets, and suggest commands.
- Treat generated commands as suggestions and review them before running.
