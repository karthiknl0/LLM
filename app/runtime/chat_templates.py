"""Runtime-specific chat prompt templates."""

from __future__ import annotations

from typing import Any

SUPPORTED_TEMPLATES = {"plain", "chatml", "llama3", "mistral", "qwen"}


def _content(message: dict[str, Any]) -> str:
    return str(message.get("content") or "")


def format_chat_messages(messages: list[dict[str, Any]], template: str = "plain") -> str:
    """Format chat messages into one prompt string for completion-only runtimes."""
    name = (template or "plain").lower().strip()
    if name not in SUPPORTED_TEMPLATES:
        raise ValueError(f"Unsupported chat template {template!r}. Supported: {sorted(SUPPORTED_TEMPLATES)}")

    if name == "plain":
        parts = []
        for msg in messages:
            role = str(msg.get("role") or "user").title()
            parts.append(f"{role}: {_content(msg)}")
        parts.append("Assistant:")
        return "\n\n".join(parts)

    if name in {"chatml", "qwen"}:
        text = ""
        for msg in messages:
            role = str(msg.get("role") or "user")
            text += f"<|im_start|>{role}\n{_content(msg)}<|im_end|>\n"
        text += "<|im_start|>assistant\n"
        return text

    if name == "llama3":
        text = "<|begin_of_text|>"
        for msg in messages:
            role = str(msg.get("role") or "user")
            text += f"<|start_header_id|>{role}<|end_header_id|>\n\n{_content(msg)}<|eot_id|>"
        text += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return text

    if name == "mistral":
        system = ""
        rounds: list[str] = []
        pending_user = ""
        for msg in messages:
            role = str(msg.get("role") or "user")
            content = _content(msg)
            if role == "system":
                system = f"{system}\n{content}".strip()
            elif role == "user":
                pending_user = f"{system}\n\n{content}".strip() if system else content
                system = ""
            elif role == "assistant" and pending_user:
                rounds.append(f"[INST] {pending_user} [/INST] {content}")
                pending_user = ""
        if pending_user:
            rounds.append(f"[INST] {pending_user} [/INST]")
        return "\n".join(rounds)

    raise AssertionError(f"Unhandled template: {name}")
