"""FastAPI server for Local AI Hub.

Provides a small local API surface that is compatible with common local and
OpenAI-style clients while reusing the configured model runtime.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.model_packages import (
    list_packages,
    package_messages,
    package_options,
    resolve_model_or_package,
)
from app.models import list_models
from app.runtime import runtime
from app.session.modelstate import current_model, installed_models


app = FastAPI(
    title="Local AI Hub API",
    version="0.1.0",
    description="Local runtime-backed API for chat, generation, and model listing.",
)


class ChatMessage(BaseModel):
    role: str
    content: str


class LocalChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    stream: bool = True
    options: dict[str, Any] | None = None


class LocalGenerateRequest(BaseModel):
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


def _resolve_request_model(name: str | None):
    requested = _model_or_default(name)
    runtime_model, package = resolve_model_or_package(requested)
    return runtime_model or requested, package, requested


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
        rt = runtime()
        models = installed_models()
        runtime_ok = True
        error = None
    except Exception as exc:
        rt = None
        models = []
        runtime_ok = False
        error = str(exc)
    return {
        "status": "ok" if runtime_ok else "degraded",
        "runtime": rt.name if rt else None,
        "active_model": current_model(),
        "models": models,
        "packages": [p.name for p in list_packages()],
        "error": error,
    }


@app.get("/api/tags")
def api_tags() -> dict[str, Any]:
    """Runtime-compatible model list endpoint."""
    try:
        rt = runtime()
        if hasattr(rt, "list_raw"):
            return rt.list_raw()
        return {"models": rt.list_models()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Runtime unavailable: {exc}") from exc


@app.get("/api/models")
def api_models() -> dict[str, Any]:
    """Local AI Hub normalized model and package metadata endpoint."""
    return {
        "runtime": runtime().name,
        "active_model": current_model(),
        "models": [m.to_dict() for m in list_models(include_embeddings=True)],
        "packages": [p.to_dict() for p in list_packages()],
    }


@app.get("/api/packages")
def api_packages() -> dict[str, Any]:
    """List LocalModel package presets."""
    return {"packages": [p.to_dict() for p in list_packages()]}


@app.get("/v1/models")
def v1_models() -> dict[str, Any]:
    """OpenAI-compatible model list endpoint with local metadata extras."""
    now = int(time.time())
    runtime_models = [
        {
            "id": model.name,
            "object": "model",
            "created": now,
            "owned_by": "local-ai-hub",
            "local_ai_hub": {
                "type": "runtime_model",
                "runtime": model.runtime,
                "capabilities": model.capabilities,
                "size": model.size,
                "family": model.family,
                "modified_at": model.modified_at,
            },
        }
        for model in list_models(include_embeddings=False)
    ]
    packages = [
        {
            "id": package.name,
            "object": "model",
            "created": now,
            "owned_by": "local-ai-hub",
            "local_ai_hub": {
                "type": "package",
                "runtime": runtime().name,
                "base": package.base,
                "capabilities": package.capabilities,
                "path": package.path,
                "description": package.description,
            },
        }
        for package in list_packages()
    ]
    return {"object": "list", "data": runtime_models + packages}


@app.post("/api/chat")
def api_chat(request: LocalChatRequest):
    """Local runtime-compatible chat endpoint."""
    model, package, _requested = _resolve_request_model(request.model)
    messages = package_messages(package, [m.model_dump() for m in request.messages])
    options = package_options(package, request.options)

    if not request.stream:
        try:
            return runtime().chat(
                model=model,
                messages=messages,
                stream=False,
                options=options,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def events() -> Iterable[str]:
        try:
            for part in runtime().chat(
                model=model,
                messages=messages,
                stream=True,
                options=options,
            ):
                yield json.dumps(part, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.post("/api/generate")
def api_generate(request: LocalGenerateRequest):
    """Local runtime-compatible text generation endpoint."""
    model, package, _requested = _resolve_request_model(request.model)
    options = package_options(package, request.options)
    system = request.system or (package.system if package else None)
    kwargs: dict[str, Any] = {
        "model": model,
        "prompt": request.prompt,
        "stream": request.stream,
        "options": options,
    }
    if system:
        kwargs["system"] = system

    if not request.stream:
        try:
            return runtime().generate(**kwargs)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def events() -> Iterable[str]:
        try:
            for part in runtime().generate(**kwargs):
                yield json.dumps(part, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.post("/v1/chat/completions")
def v1_chat_completions(request: OpenAIChatRequest):
    """OpenAI-compatible chat completion endpoint."""
    model, package, requested = _resolve_request_model(request.model)
    messages = package_messages(package, [m.model_dump() for m in request.messages])
    options = package_options(package, _chat_options_from_request(request))

    if request.stream:
        def events() -> Iterable[str]:
            try:
                for part in runtime().chat(
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
                            "model": requested,
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
                        "model": requested,
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
        response = runtime().chat(
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
        "model": requested,
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
