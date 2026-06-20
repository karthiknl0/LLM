"""Core agent execution helpers and the one-shot tool-calling loop."""

import json

import ollama

from app.agent.modes import MAX_TOOL_ROUNDS
from app.agent.prompt import skill_hints
from app.content.instructions import standing_instructions
from app.content.playbooks import catalog_hint
from app.services.hooks import pre_tool
from app.session.modelstate import current_model
from app.skills import maybe_learn


def answer_text(msg) -> str:
    """Final reply text. gemma4 in the tool loop sometimes leaves `content`
    empty and puts its answer in the separate `thinking` field — fall back
    to that so the user never gets a blank reply."""
    return (msg["content"] or getattr(msg, "thinking", "") or "").strip()


def call_sig(call) -> str:
    """Stable signature of a tool call, to detect a model repeating itself."""
    fn = call["function"]
    return fn["name"] + ":" + json.dumps(dict(fn["arguments"] or {}), sort_keys=True, default=str)


def force_answer(messages) -> str:
    """gemma4 sometimes gathers info but never concludes. Ask once, plainly,
    for the final answer with no further tools."""
    messages = messages + [{
        "role": "user",
        "content": "Now write your final answer for me based on everything you "
        "gathered above. Be specific and do not call any tools.",
    }]
    return answer_text(
        ollama.chat(model=current_model(), messages=messages, think=False)["message"]
    )


def conclude(msg, messages) -> str:
    """Best final answer: the model's own content; else a forced no-tools
    answer (gemma4 often gathers info but leaves content empty); else its
    raw thinking as a last resort. Never returns blank."""
    content = (msg["content"] or "").strip()
    if content:
        return content
    return force_answer(messages) or (getattr(msg, "thinking", "") or "").strip()


def run_with_tools(system: str, user: str, max_rounds: int = MAX_TOOL_ROUNDS) -> str:
    """One-shot tool-using conversation, for other modules (team mode):
    same tools as the Agent tab, no streaming."""
    from app.tools.registry import all_tools, all_functions

    rules = standing_instructions()
    if rules:
        system += "\n\nThe user's standing instructions (always follow):\n" + rules
    messages = [
        {"role": "system", "content": system + skill_hints(user) + catalog_hint()},
        {"role": "user", "content": user},
    ]
    tools, functions = all_tools(), all_functions()
    executed_code = []
    reply = "(no answer)"
    seen_calls = set()
    for round_number in range(max_rounds + 1):
        response = ollama.chat(
            model=current_model(), messages=messages, tools=tools, think=False
        )
        msg = response["message"]
        tool_calls = getattr(msg, "tool_calls", None) or []
        fresh = [c for c in tool_calls if call_sig(c) not in seen_calls]
        if not fresh or round_number == max_rounds:
            reply = conclude(msg, messages)
            break
        messages.append(msg)
        for call in fresh:
            seen_calls.add(call_sig(call))
            name = call["function"]["name"]
            arguments = dict(call["function"]["arguments"] or {})
            block = pre_tool(name, arguments)
            if block:
                result = block
            else:
                try:
                    result = functions[name](**arguments)
                except Exception as exc:
                    result = f"Tool failed: {exc}"
            if name == "run_python" and arguments.get("code"):
                executed_code.append(arguments["code"])
            messages.append(
                {"role": "tool", "content": str(result)[:8000], "name": name}
            )
    maybe_learn(user, executed_code)
    return reply
