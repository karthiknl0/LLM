# Local AI Hub API

The Local AI Hub API is a small FastAPI server that exposes Ollama-compatible and OpenAI-compatible endpoints.

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

Returns runtime status, active model, installed models, and any Ollama connection error.

## Ollama-compatible endpoints

### List models

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

Streaming responses use newline-delimited JSON, similar to Ollama.

## OpenAI-compatible endpoints

### List models

```bash
curl http://127.0.0.1:11435/v1/models
```

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

- The API currently uses Ollama as the runtime.
- Token usage values are placeholders for now.
- API auth is not implemented yet. Keep it bound to `127.0.0.1` unless you trust your network.
- The next roadmap step is to move model operations behind a runtime abstraction so API, CLI, UI, and RAG all use one interface.
