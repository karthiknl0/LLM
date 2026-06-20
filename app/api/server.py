"""FastAPI server for Local AI Hub.

Provides a small local API surface that is compatible with common Ollama and
OpenAI-style clients while reusing the current Ollama-backed model runtime.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from typing import Any

import ollama
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.session.modelstate import current_model, installed_models


app = FastAPI(
    title="Local AI Hub API",
    version="0.1.0",
    description="Local Ollama-backed API for chat, generation, and model listing.",
)


class ChatMessage(BaseModel):
    role: str
    content: str


class OllamaChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    stream: bool = True
    options: dict[str, Any] | None = None


class OllamaGenerateRequest(BaseModel):
    model: str | None = None
    prompt: str
    system: str | None = None
    stream: bool = True
    options: dict[str, Any] | None = None


class OpenAIChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = Field(default=None, alias="max_tokens")


def _model_or_default(name: str | None) -> str:
    return (name or current_model()).strip()


def _chat_options_from_request(request: OpenAIChatRequest) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.top_p is not None:
        options["top_p"] = request.top_p
    if request.max_tokens is not None:
        options["num_predict"] = request.max_tokens
    return options


def _sse(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/health")
def health() -> dict[str, Any]:
    try:
        models = installed_models()
        ollama_ok = True
        error = None
    except Exception as exc:
        models = []
        ollama_ok = False
        error = str(exc)
    return {
        "status": "ok" if ollama_ok else "degraded",
        "runtime": "ollama",
        "active_model": current_model(),
        "models": models,
        "error": error,
    }


@app.get("/api/tags")
def api_tags() -> dict[str, Any]:
    """Ollama-compatible model list endpoint."""
    try:
        return ollama.list()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {exc}") from exc


@app.get("/v1/models")
def v1_models() -> dict[str, Any]:
    """OpenAI-compatible model list endpoint."""
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "created": now,
                "owned_by": "local-ai-hub",
            }
            for model in installed_models()
        ],
    }


@app.post("/api/chat")
def api_chat(request: OllamaChatRequest):
    """Ollama-compatible chat endpoint."""
    model = _model_or_default(request.model)
    messages = [m.model_dump() for m in request.messages]

    if not request.stream:
        try:
            return ollama.chat(
                model=model,
                messages=messages,
                stream=False,
                options=request.options,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def events() -> Iterable[str]:
        try:
            for part in ollama.chat(
                model=model,
                messages=messages,
                stream=True,
                options=request.options,
            ):
                yield json.dumps(part, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.post("/api/generate")
def api_generate(request: OllamaGenerateRequest):
    """Ollama-compatible text generation endpoint."""
    model = _model_or_default(request.model)
    kwargs: dict[str, Any] = {
        "model": model,
        "prompt": request.prompt,
        "stream": request.stream,
        "options": request.options,
    }
    if request.system:
        kwargs["system"] = request.system

    if not request.stream:
        try:
            return ollama.generate(**kwargs)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def events() -> Iterable[str]:
        try:
            for part in ollama.generate(**kwargs):
                yield json.dumps(part, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.post("/v1/chat/completions")
def v1_chat_completions(request: OpenAIChatRequest):
    """OpenAI-compatible chat completion endpoint."""
    model = _model_or_default(request.model)
    messages = [m.model_dump() for m in request.messages]
    options = _chat_options_from_request(request) or None

    if request.stream:
        def events() -> Iterable[str]:
            try:
                for part in ollama.chat(
                    model=model,
                    messages=messages,
                    stream=True,
                    options=options,
                ):
                    content = part.get("message", {}).get("content", "")
                    if not content:
                        continue
                    yield _sse(
                        {
                            "id": f"chatcmpl-{int(time.time() * 1000)}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": content},
                                    "finish_reason": None,
                                }
                            ],
                        }
                    )
                yield _sse(
                    {
                        "id": f"chatcmpl-{int(time.time() * 1000)}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                )
                yield "data: [DONE]\n\n"
            except Exception as exc:
                yield _sse({"error": {"message": str(exc), "type": "server_error"}})
                yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            stream=False,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    content = response["message"]["content"]
    return {
        "id": f"chatcmpl-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }
