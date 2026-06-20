# LocalModel Packages

`LocalModel.yaml` files define named local model presets. A package points to a base runtime model and adds defaults such as a system prompt, generation parameters, capabilities, and future RAG/tool settings.

## Location

Local AI Hub looks for package files in these places:

```text
LocalModel.yaml
LocalModel.yml
data/models/<package-name>/LocalModel.yaml
data/models/<package-name>/LocalModel.yml
```

## Example

```yaml
name: saree-assistant
description: Assistant for saree manufacturing, inventory, sales, and design workflows.
base: qwen3.5:4b
system: |
  You are a helpful assistant for saree manufacturing, stock planning,
  sales follow-up, design ideas, and customer communication.
parameters:
  temperature: 0.4
  top_p: 0.9
capabilities:
  - chat
  - code
  - vision
rag:
  collections:
    - documents
tools:
  - documents
```

## CLI

Install a package file:

```bash
local-ai create -f LocalModel.yaml
local-ai create -f LocalModel.yaml --activate
```

See `docs/LOCALMODEL_CREATE.md` for details.

List packages:

```bash
local-ai packages
```

Inspect a package:

```bash
local-ai inspect saree-assistant
```

Run a package:

```bash
local-ai run --model saree-assistant "Draft a WhatsApp follow-up for a customer"
```

Use a package for interactive chat:

```bash
local-ai chat --model saree-assistant
```

Set a package as the active model preset:

```bash
local-ai model saree-assistant
local-ai chat
```

## API

List packages and runtime models:

```bash
curl http://127.0.0.1:11435/api/models
curl http://127.0.0.1:11435/api/packages
```

Use a package with the OpenAI-compatible endpoint:

```bash
curl http://127.0.0.1:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "saree-assistant",
    "messages": [
      {"role": "user", "content": "Create a short product description for a silk saree"}
    ]
  }'
```

## Fields

### `name`

The package name used in CLI/API calls.

### `base`

The installed runtime model to use under the hood.

### `system`

A system prompt prepended to chat calls.

### `parameters`

Default generation parameters passed to the runtime. Request-level parameters override package defaults.

### `capabilities`

Human-readable capabilities such as `chat`, `code`, `vision`, or `reasoning`.

### `rag`

Reserved for package-specific retrieval defaults.

### `tools`

Reserved for package-specific tool defaults.

## Notes

- Packages do not copy or redistribute model files.
- Packages are local presets over installed runtime models.
- Package names appear in `/v1/models` alongside runtime models.
