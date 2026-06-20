"""Agent main loop: streaming generator for the Agent tab."""

import shutil
from pathlib import Path

import ollama

from app.agent.modes import IMAGE_EXTENSIONS, MAX_TOOL_ROUNDS, PLAN_MODE_PROMPT, READ_ONLY_TOOLS
from app.agent.prompt import SYSTEM_PROMPT, skill_hints
from app.agent.runner import answer_text, call_sig, conclude, force_answer
from app.chat.stream import _log_turn
from app.content.notes import read_notes, recent_notes
from app.content.playbooks import catalog_hint
from app.core.config import WORKSPACE_DIR
from app.core.project import active_project_folder, active_project_label, set_project_folder
from app.media.vision import VIDEO_EXTENSIONS, analyze_media
from app.memory import recall, recall_lessons, remember
from app.services.hooks import post_reply, pre_tool
from app.session.modelstate import current_model
from app.skills import maybe_learn
from app.tools.registry import TOOL_STATUS, all_tools, all_functions


def _describe_attachments(files: list[str], question: str) -> tuple[list[str], list[str]]:
    """Turn attached files into context: images/videos go through the
    vision model; everything else is copied to the workspace so
    run_python can use it. Returns (notes, vision_analyses) — the raw
    vision text is kept separately so it can stand in as the answer if the
    chat model stubs on a long/repetitive analysis."""
    notes, vision = [], []
    for path in files[:3]:
        name = Path(path).name
        suffix = Path(path).suffix.lower()
        if suffix in IMAGE_EXTENSIONS or suffix in VIDEO_EXTENSIONS:
            analysis = analyze_media(path, question or "Describe this in detail.")
            notes.append(f"[Attached '{name}' — vision model analysis: {analysis}]")
            vision.append(analysis)
        else:
            try:
                project_dir = active_project_folder(WORKSPACE_DIR)
                shutil.copy(path, project_dir / name)
                notes.append(
                    f"[Attached file saved to the project as '{name}' — "
                    "use run_python to read it.]"
                )
            except Exception as exc:
                notes.append(f"[Could not save attachment '{name}': {exc}]")
    return notes, vision


def agent_chat(
    message, history: list[dict], project_folder: str = "",
    deep_answer: bool = False, plan_mode: bool = False,
):
    """Generator for the Agent tab: yields tool-use progress, then the
    final answer. With deep_answer, the model reviews and corrects its
    own draft before replying (slower, more reliable). With plan_mode,
    editing/execution tools are removed and the agent proposes a plan."""
    files = []
    if isinstance(message, dict):  # multimodal input: {"text", "files"}
        files = list(message.get("files") or [])
        message = (message.get("text") or "").strip()
    if not message and not files:
        yield "Say something or attach a file."
        return
    ok, project_status = set_project_folder(project_folder)
    if not ok:
        yield project_status
        return
    if not files:
        if message.strip().lower() == "/compact":
            from app.chat.history import manual_compact

            yield manual_compact(history)
            return
        if message.strip().lower() == "/export":
            from app.commands import export_chat

            yield export_chat(history)
            return
        from app.commands import handle_command

        command_reply = handle_command(message)
        if command_reply is not None:
            yield command_reply
            return

    # Render an assistant bubble immediately. The first Ollama call may take
    # several seconds on local hardware, especially when the model is loading.
    yield "*Thinking…*"

    system = SYSTEM_PROMPT
    memories = recall(message) if message else []
    system += f"\n\nActive project folder: {active_project_label()}"
    if memories:
        system += "\n\nThings you remember about the user:\n"
        system += "\n".join(f"- {m}" for m in memories)
    lessons = recall_lessons(message) if message else []
    if lessons:
        system += "\n\nStanding instructions learned from past corrections:\n"
        system += "\n".join(f"- {lesson}" for lesson in lessons)
    system += skill_hints(message)
    notes_tail = recent_notes()
    if notes_tail:
        system += "\n\nYour recent scratchpad notes:\n" + notes_tail
    system += catalog_hint()

    if plan_mode:
        system += PLAN_MODE_PROMPT
    from app.chat.history import compact_history
    summary, past_messages = compact_history(history)
    if summary:
        system += "\n\nSummary of earlier parts of this conversation:\n" + summary
    messages = [{"role": "system", "content": system}] + past_messages
    steps = []
    user_content = message
    vision_analyses = []
    if files:
        steps.append("*Looking at the attachment…*")
        yield "\n\n".join(steps)
        notes, vision_analyses = _describe_attachments(files, message)
        user_content = (message + "\n\n" + "\n".join(notes)).strip()
    messages.append({"role": "user", "content": user_content})

    tools, functions = all_tools(), all_functions()
    if files:  # the user attached the media directly — capturing the live
        # screen is the wrong tool (and returns blank), so remove it. The
        # vision model's analysis of the attachment is already in context.
        tools = [t for t in tools if t["function"]["name"] != "look_at_screen"]
        functions = {k: v for k, v in functions.items() if k != "look_at_screen"}
    if plan_mode:  # hard guarantee, not just a prompt: write tools removed
        tools = [t for t in tools if t["function"]["name"] in READ_ONLY_TOOLS]
        functions = {k: v for k, v in functions.items() if k in READ_ONLY_TOOLS}
    reply = "(no answer)"
    executed_code = []
    prefix = ("\n\n".join(steps) + "\n\n") if steps else ""

    if vision_analyses:
        # Media attachment: the vision model already produced the analysis.
        # Answer directly with a lean prompt and NO tools — the coding-agent
        # tool loop derails the small model on images (it stubs, or treats
        # "analyze the image" as a code-inspection task and goes browsing
        # files). Stream the reply; if the model still stubs, fall back to
        # the vision analysis itself, which is already a complete answer.
        direct = [
            {"role": "system", "content":
                "You are a helpful assistant. The user attached an image or "
                "video; a vision model's analysis of it is included in their "
                "message between brackets. Answer the user's request about "
                "the attachment using that analysis. Be specific and concise."},
            {"role": "user", "content": user_content},
        ]
        reply = ""
        for part in ollama.chat(
            model=current_model(), messages=direct, think=False, stream=True,
        ):
            tok = part["message"].get("content")
            if tok:
                reply += tok
                yield prefix + reply
        reply = reply.strip() if len(reply.strip()) >= 40 else "\n\n".join(vision_analyses)
    else:
        seen_calls = set()
        for _round in range(MAX_TOOL_ROUNDS + 1):
            # Stream the call: tool-deciding rounds send no content (just tool
            # calls), so nothing shows; the final answer round streams its
            # tokens live so the user watches the reply appear, not a spinner.
            content = ""
            tool_calls = []
            for part in ollama.chat(
                model=current_model(), messages=messages, tools=tools,
                think=False, stream=True,
            ):
                m = part["message"]
                if m.get("content"):
                    content += m["content"]
                    yield prefix + content
                if m.get("tool_calls"):
                    tool_calls.extend(m["tool_calls"])
            msg = {"role": "assistant", "content": content, "tool_calls": tool_calls}
            # Act only on tool calls not already run this turn — a model can
            # loop on the same call (e.g. list_files) instead of concluding.
            fresh = [c for c in tool_calls if call_sig(c) not in seen_calls]
            if not fresh or _round == MAX_TOOL_ROUNDS:
                reply = content.strip() or conclude(msg, messages)
                break

            messages.append(msg)
            for call in fresh:
                seen_calls.add(call_sig(call))
                name = call["function"]["name"]
                arguments = dict(call["function"]["arguments"] or {})
                steps.append(f"*{TOOL_STATUS.get(name, 'Using ' + name.replace('_', ' '))}…*")
                yield "\n\n".join(steps)
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
            prefix = ("\n\n".join(steps) + "\n\n") if steps else ""

    if deep_answer and reply.strip() and not vision_analyses:
        steps.append("*Reviewing the draft answer…*")
        yield "\n\n".join(steps)
        messages.append({"role": "assistant", "content": reply})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Review your answer above before I see it: check for "
                    "factual errors, parts of my question you missed, and "
                    "unsupported claims. Then output ONLY the corrected "
                    "final answer — no commentary about the review."
                ),
            }
        )
        review = ollama.chat(model=current_model(), messages=messages, think=False)
        revised = answer_text(review["message"])
        if revised:
            reply = revised

    if steps:
        reply = "\n\n".join(steps) + "\n\n" + reply
    yield reply

    _log_turn(message, reply)
    remember(message, reply)
    maybe_learn(message, executed_code)
    post_reply(reply)
