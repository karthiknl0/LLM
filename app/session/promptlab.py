"""Prompt Helper: rewrite a rough prompt using the core techniques from
Anthropic's prompt-engineering tutorial — clear/direct instructions, a
role, data separated from instructions, explicit output format, a
step-by-step cue, and few-shot examples when useful.

Useful for authoring the personas, playbooks, and eval criteria the rest
of the hub runs on. Runs on the local model.
"""

import re

import ollama

from app.session.modelstate import current_model

IMPROVE_SYSTEM = (
    "You are a prompt engineer. Rewrite the user's prompt so a language "
    "model follows it reliably, applying these techniques only where they "
    "help: be clear and direct; assign a role; separate any input data "
    "from the instructions (use tags like <data></data>); specify the "
    "output format; add a brief 'think step by step' cue for reasoning "
    "tasks; include one short example if it removes ambiguity. Do not "
    "invent requirements the user didn't state.\n\n"
    "Reply in exactly two sections:\n"
    "## Improved prompt\n<the rewritten prompt>\n\n"
    "## What changed\n<3-5 short bullets naming the techniques you applied>"
)


def improve_prompt(draft: str) -> str:
    if not (draft or "").strip():
        return "Paste a prompt to improve."
    response = ollama.chat(
        model=current_model(),
        messages=[
            {"role": "system", "content": IMPROVE_SYSTEM},
            {"role": "user", "content": draft.strip()},
        ],
    )
    return re.sub(
        r"<think>.*?</think>", "", response["message"]["content"], flags=re.DOTALL
    ).strip()
