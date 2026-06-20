# Local AI Hub API

The Local AI Hub API is a small FastAPI server that exposes local-runtime and OpenAI-compatible endpoints.

Start it with:

```bash
local-ai api
```

By default it listens on:

```text
http://127.0.0.1:11435
```

OpenAI-compatible base URL:

```text
http://127.0.0.1:11435/v1
```

Override host and port:

```bash
local-ai api --host 0.0.0.0 --port 11435
```

Environment variables:

```bash
AIHUB_API_HOST=0.0.0.0
AIHUB_API_PORT=11435
```

## Health

```bash
curl http://127.0.0.1:11435/health
```

Returns runtime status, active model/package, installed models, packages, and any runtime connection error.

## Local AI Hub endpoints

### Normalized model and package metadata

```bash
curl http://127.0.0.1:11435/api/models
```

Returns active model/package, runtime, normalized metadata for installed models, and LocalModel packages.

### LocalModel packages

```bash
curl http://127.0.0.1:11435/api/packages
```

Returns package presets from `LocalModel.yaml` files.

## Runtime-compatible endpoints

### List runtime models

```bash
curl http://127.0.0.1:11435/api/tags
```

### Chat

```bash
curl http://127.0.0.1:11435/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:4b",
    "stream": false,
    "messages": [
      {"role": "user", "content": "Explain RAG in simple words"}
    ]
  }'
```

Use a LocalModel package by passing the package name as `model`:

```bash
curl http://127.0.0.1:11435/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "saree-assistant",
    "stream": false,
    "messages": [
      {"role": "user", "content": "Write a customer follow-up"}
    ]
  }'
```

### Generate

```bash
curl http://127.0.0.1:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:4b",
    "stream": false,
    "prompt": "Write a short product description for a silk saree"
  }'
```

Streaming responses use newline-delimited JSON.

## OpenAI-compatible endpoints

### List models and packages

```bash
curl http://127.0.0.1:11435/v1/models
```

The response includes standard OpenAI-style model fields plus a `local_ai_hub` object with type, runtime, capabilities, size, family, package base, and path where available.

### Chat completions

```bash
curl http://127.0.0.1:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:4b",
    "messages": [
      {"role": "user", "content": "Write a Python function to parse CSV files"}
    ],
    "temperature": 0.3
  }'
```

### Chat completions with a LocalModel package

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

### Streaming chat completions

```bash
curl http://127.0.0.1:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:4b",
    "stream": true,
    "messages": [
      {"role": "user", "content": "Give me three startup ideas for local AI"}
    ]
  }'
```

Streaming responses use server-sent events and end with:

```text
data: [DONE]
```

## OpenAI Python SDK example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:11435/v1",
    api_key="local-ai-hub",
)

response = client.chat.completions.create(
    model="qwen3.5:4b",
    messages=[
        {"role": "user", "content": "Explain what this project does"},
    ],
)

print(response.choices[0].message.content)
```

## Notes

- The API currently uses the configured local runtime. Ollama is the default backend implementation.
- Package names can be used anywhere a chat model name is accepted.
- Token usage values are placeholders for now.
- API auth is not implemented yet. Keep it bound to `127.0.0.1` unless you trust your network.
