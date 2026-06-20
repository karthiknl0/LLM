# llama.cpp Runtime Path

Local AI Hub includes an optional `llamacpp` runtime path for direct GGUF model files.

The default production backend remains `ollama`. Use `llamacpp` only when you want to experiment with direct `.gguf` files.

## Status

Implemented:

- Discover `.gguf` files in `data/gguf/`.
- Show discovered models through `local-ai list`.
- Run `generate` and `chat` when the optional `llama-cpp-python` package is installed.
- Keep tests lightweight by using fake backend objects in CI.

Not implemented yet:

- Embeddings for RAG.
- Pulling/downloading models.
- Deleting model files.
- Advanced chat templates.
- Runtime-specific UI controls.

## Model location

Place GGUF files here:

```text
data/gguf/
```

Nested folders are supported:

```text
data/gguf/demo.gguf
data/gguf/qwen/qwen-test.gguf
```

Model names are derived from the relative path without `.gguf`:

```text
demo
qwen/qwen-test
```

## List GGUF models

```bash
AIHUB_RUNTIME=llamacpp local-ai list
```

## Optional dependency

Install `llama-cpp-python` only when you want to run this backend.

```bash
pip install llama-cpp-python
```

For GPU acceleration, install the variant that matches your system and hardware.

## Run generation

```bash
AIHUB_RUNTIME=llamacpp local-ai run --model demo "Write a short introduction"
```

## Chat

```bash
AIHUB_RUNTIME=llamacpp local-ai chat --model demo
```

## API

```bash
AIHUB_RUNTIME=llamacpp local-ai api
```

Then call:

```http
POST /v1/chat/completions
```

with the GGUF model name.

## Notes

- This path is experimental.
- The default backend is still recommended for normal use.
- RAG still needs the default embedding runtime until llama.cpp embedding support is added.
- Large GGUF models may exceed your available RAM or VRAM.
