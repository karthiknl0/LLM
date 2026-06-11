"""Agent mode: one chat where the model decides for itself when to
search your documents, research the web, or generate an image — using
Ollama's native tool calling. Fully local routing.
"""

import shutil
from pathlib import Path

import ollama

from app import gittools, imagegen, mcp_client, rag, research, sandbox, screen, skills
from app.browser import verify_in_browser
from app.chat import _log_turn
from app.config import CHAT_MODEL, WORKSPACE_DIR
from app.fileedit import propose_edit, read_file
from app.history import compact_history
from app.memory import recall, recall_lessons, remember
from app.notes import read_notes, recent_notes, take_note
from app.playbooks import catalog_hint, load_playbook
from app.vision import VIDEO_EXTENSIONS, analyze_media

MAX_TOOL_ROUNDS = 6
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

SYSTEM_PROMPT = (
    "You are a helpful local AI assistant running entirely on the user's "
    "own computer, with tools. Use search_documents for questions about "
    "the user's own files, web_research for current events or anything "
    "you're unsure about, generate_image when asked to create a picture, "
    "and run_python for any calculation, data analysis, or file "
    "processing — never do arithmetic in your head. If run_python returns "
    "an error, read the error message, fix the code, and run it again — "
    "don't give up after one failure. Use look_at_screen when the user "
    "refers to what is currently on their screen. For git work: "
    "git_clone a repo, edit its files under repos/<name>/ with "
    "run_python, commit to an ai/ branch with git_commit, and call "
    "git_push ONLY when the user explicitly asks to push — the push "
    "creates a branch they review as a pull request. For files outside "
    "the workspace (the user's own documents/configs): read_file to "
    "inspect, propose_edit to suggest a change — edits apply ONLY after "
    "the user approves the diff in the Approvals tab, so always tell "
    "them an edit is waiting there. During long "
    "multi-step tasks, use take_note to record progress, decisions, and "
    "next steps — notes survive even when older conversation is "
    "summarized away — and read_notes to recall them. Answer directly "
    "from your own knowledge when no tool is needed. Be concise and "
    "practical.\n\n"
    "When writing or editing code: state your assumptions instead of "
    "guessing silently, and ask when truly unsure. Write the minimum "
    "code that solves the problem — no speculative features or "
    "abstractions. Change only what the task requires; match the "
    "existing style and never rewrite unrelated code. Verify before "
    "declaring done: after editing code in a cloned repo, build and test "
    "it with run_command (e.g. 'pytest -q', 'npm test', 'npm run build', "
    "with cwd set to repos/<name>) and fix any failures before "
    "finishing — for bug fixes, run the test that reproduces the bug "
    "first, then show it passing. After building or changing anything "
    "with a web page, verify_in_browser it (use file:// for HTML files "
    "in the workspace) and fix what the check reveals before answering."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Search the user's own indexed files (PDFs, spreadsheets, "
                "code). Returns the most relevant passages with file names."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to look for"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_research",
            "description": (
                "Search the web and read the top pages. Returns a cited "
                "summary. Use for current events or facts you're unsure of."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Research question"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": (
                "Execute Python code and return its output. Use for math, "
                "data analysis, and file processing. The working directory "
                "is the user's workspace folder (data/workspace/) — read "
                "and write files there, print() results, and save plots "
                "as .png files. pandas and matplotlib are available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to run"}
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a file anywhere in the user's allowed folders (their "
                "home directory by default). Use absolute paths."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_edit",
            "description": (
                "Propose new content for a file in the user's allowed "
                "folders. NOT applied immediately: the user reviews the "
                "diff in the Approvals tab and approves or rejects it. "
                "Provide the COMPLETE new file content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"},
                    "new_content": {
                        "type": "string",
                        "description": "Full new content of the file",
                    },
                    "reason": {
                        "type": "string",
                        "description": "One line: what changed and why",
                    },
                },
                "required": ["path", "new_content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a build, test, or shell command inside the workspace "
                "and get its output and exit code. Set cwd to the repo "
                "folder (e.g. repos/<name>). Use to build and test code "
                "you edit: pytest, npm test, npm run build, make, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "cwd": {
                        "type": "string",
                        "description": "Dir under the workspace, e.g. repos/myrepo",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_clone",
            "description": "Clone a git repository into the workspace so its files can be read and edited.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Repository URL"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Show the current branch and uncommitted changes of a cloned repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository folder name"}
                },
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": (
                "Commit all changes in a cloned repository to a branch. "
                "The branch must be named ai/<short-description>."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository folder name"},
                    "branch": {"type": "string", "description": "Branch like ai/fix-typo"},
                    "message": {"type": "string", "description": "Commit message"},
                },
                "required": ["repo", "branch", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_push",
            "description": (
                "Push the current ai/ branch of a cloned repository so the "
                "user can open a pull request. Only use when the user "
                "explicitly asks to push."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository folder name"}
                },
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_note",
            "description": (
                "Append a note to your persistent scratchpad. Use during "
                "long tasks to record progress, decisions, findings, and "
                "next steps so they survive context compaction."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The note"}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_notes",
            "description": "Read your scratchpad of notes from current and past tasks.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_playbook",
            "description": (
                "Load the full step-by-step workflow of a named playbook "
                "before doing that kind of task. Names are listed in your "
                "system prompt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Playbook name"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_in_browser",
            "description": (
                "Open a URL in a headless browser, screenshot it, analyze "
                "it with the vision model, and report visible text plus "
                "console errors. Use to verify web pages you built or "
                "changed (file:///path or http://localhost:port) and to "
                "check live sites visually."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "http(s):// or file:// URL to check",
                    },
                    "question": {
                        "type": "string",
                        "description": "What to verify on the page",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "look_at_screen",
            "description": (
                "Capture the user's current screen and analyze it with the "
                "vision model. Use when the user asks about something on "
                "their screen right now (an error, a window, a page)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "What to look for on the screen",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Create an image from a text prompt and save it to disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image description"}
                },
                "required": ["prompt"],
            },
        },
    },
]


def _run_search_documents(query: str) -> str:
    retrieved = rag.retrieve_context(query)
    if retrieved is None:
        return "No indexed documents (or nothing relevant). The user can add files to data/documents/ and index them in the Documents tab."
    context, _sources = retrieved
    return context


def _run_web_research(query: str) -> str:
    return research.research(query)


def _run_generate_image(prompt: str) -> str:
    _image, status = imagegen.generate_image(prompt)
    return f"Image generated. {status} Tell the user where it was saved."


TOOL_FUNCTIONS = {
    "search_documents": _run_search_documents,
    "web_research": _run_web_research,
    "generate_image": _run_generate_image,
    "run_python": sandbox.run_python,
    "look_at_screen": screen.look_at_screen,
    "verify_in_browser": verify_in_browser,
    "take_note": take_note,
    "read_notes": read_notes,
    "load_playbook": load_playbook,
    "run_command": sandbox.run_command,
    "read_file": read_file,
    "propose_edit": propose_edit,
    "git_clone": gittools.git_clone,
    "git_status": gittools.git_status,
    "git_commit": gittools.git_commit,
    "git_push": gittools.git_push,
}

TOOL_STATUS = {
    "search_documents": "Searching your documents",
    "web_research": "Researching the web",
    "generate_image": "Generating image",
    "run_python": "Running Python code",
    "look_at_screen": "Looking at your screen",
    "verify_in_browser": "Verifying in the browser",
    "take_note": "Taking a note",
    "read_notes": "Reading notes",
    "load_playbook": "Loading a playbook",
    "run_command": "Building / running tests",
    "read_file": "Reading a file",
    "propose_edit": "Proposing a file edit (needs your approval)",
    "git_clone": "Cloning repository",
    "git_status": "Checking git status",
    "git_commit": "Committing changes",
    "git_push": "Pushing branch",
}


def _all_tools() -> list[dict]:
    """Built-in tools plus any from configured MCP servers."""
    return TOOLS + mcp_client.mcp_tools()


def _all_functions() -> dict:
    return {**TOOL_FUNCTIONS, **mcp_client.mcp_functions()}


def _skill_hints(task: str) -> str:
    """System-prompt addition listing saved skills relevant to a task."""
    hints = skills.recall_skills(task) if task else []
    if not hints:
        return ""
    return (
        "\n\nSkills you saved from past tasks — import them inside "
        "run_python instead of rewriting:\n" + "\n".join(f"- {h}" for h in hints)
    )


def run_with_tools(system: str, user: str, max_rounds: int = MAX_TOOL_ROUNDS) -> str:
    """One-shot tool-using conversation, for other modules (team mode):
    same tools as the Agent tab, no streaming."""
    messages = [
        {"role": "system", "content": system + _skill_hints(user) + catalog_hint()},
        {"role": "user", "content": user},
    ]
    tools, functions = _all_tools(), _all_functions()
    executed_code = []
    reply = "(no answer)"
    for round_number in range(max_rounds + 1):
        response = ollama.chat(model=CHAT_MODEL, messages=messages, tools=tools)
        msg = response["message"]
        tool_calls = getattr(msg, "tool_calls", None) or []
        if not tool_calls or round_number == max_rounds:
            reply = msg["content"]
            break
        messages.append(msg)
        for call in tool_calls:
            name = call["function"]["name"]
            arguments = dict(call["function"]["arguments"] or {})
            try:
                result = functions[name](**arguments)
            except Exception as exc:
                result = f"Tool failed: {exc}"
            if name == "run_python" and arguments.get("code"):
                executed_code.append(arguments["code"])
            messages.append(
                {"role": "tool", "content": str(result)[:8000], "name": name}
            )
    skills.maybe_learn(user, executed_code)
    return reply


def _describe_attachments(files: list[str], question: str) -> list[str]:
    """Turn attached files into context: images/videos go through the
    vision model; everything else is copied to the workspace so
    run_python can use it."""
    notes = []
    for path in files[:3]:
        name = Path(path).name
        suffix = Path(path).suffix.lower()
        if suffix in IMAGE_EXTENSIONS or suffix in VIDEO_EXTENSIONS:
            analysis = analyze_media(path, question or "Describe this in detail.")
            notes.append(f"[Attached '{name}' — vision model analysis: {analysis}]")
        else:
            try:
                shutil.copy(path, WORKSPACE_DIR / name)
                notes.append(
                    f"[Attached file saved to the workspace as '{name}' — "
                    "use run_python to read it.]"
                )
            except Exception as exc:
                notes.append(f"[Could not save attachment '{name}': {exc}]")
    return notes


def agent_chat(message, history: list[dict], deep_answer: bool = False):
    """Generator for the Agent tab: yields tool-use progress, then the
    final answer. With deep_answer, the model reviews and corrects its
    own draft before replying (slower, more reliable)."""
    files = []
    if isinstance(message, dict):  # multimodal input: {"text", "files"}
        files = list(message.get("files") or [])
        message = (message.get("text") or "").strip()
    if not message and not files:
        yield "Say something or attach a file."
        return
    if not files:
        if message.strip().lower() == "/compact":
            from app.history import manual_compact

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

    system = SYSTEM_PROMPT
    memories = recall(message) if message else []
    if memories:
        system += "\n\nThings you remember about the user:\n"
        system += "\n".join(f"- {m}" for m in memories)
    lessons = recall_lessons(message) if message else []
    if lessons:
        system += "\n\nStanding instructions learned from past corrections:\n"
        system += "\n".join(f"- {lesson}" for lesson in lessons)
    system += _skill_hints(message)
    notes_tail = recent_notes()
    if notes_tail:
        system += "\n\nYour recent scratchpad notes:\n" + notes_tail
    system += catalog_hint()

    summary, past_messages = compact_history(history)
    if summary:
        system += "\n\nSummary of earlier parts of this conversation:\n" + summary
    messages = [{"role": "system", "content": system}] + past_messages
    steps = []
    user_content = message
    if files:
        steps.append("*Looking at the attachment…*")
        yield "\n\n".join(steps)
        notes = _describe_attachments(files, message)
        user_content = (message + "\n\n" + "\n".join(notes)).strip()
    messages.append({"role": "user", "content": user_content})

    tools, functions = _all_tools(), _all_functions()
    reply = "(no answer)"
    executed_code = []
    for _round in range(MAX_TOOL_ROUNDS + 1):
        response = ollama.chat(model=CHAT_MODEL, messages=messages, tools=tools)
        msg = response["message"]
        tool_calls = getattr(msg, "tool_calls", None) or []

        if not tool_calls or _round == MAX_TOOL_ROUNDS:
            reply = msg["content"]
            break

        messages.append(msg)
        for call in tool_calls:
            name = call["function"]["name"]
            arguments = dict(call["function"]["arguments"] or {})
            steps.append(f"*{TOOL_STATUS.get(name, 'Using ' + name.replace('_', ' '))}…*")
            yield "\n\n".join(steps)
            try:
                result = functions[name](**arguments)
            except Exception as exc:
                result = f"Tool failed: {exc}"
            if name == "run_python" and arguments.get("code"):
                executed_code.append(arguments["code"])
            messages.append(
                {"role": "tool", "content": str(result)[:8000], "name": name}
            )

    if deep_answer and reply.strip():
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
        review = ollama.chat(model=CHAT_MODEL, messages=messages)
        revised = review["message"]["content"].strip()
        if revised:
            reply = revised

    if steps:
        reply = "\n\n".join(steps) + "\n\n" + reply
    yield reply

    _log_turn(message, reply)
    remember(message, reply)
    skills.maybe_learn(message, executed_code)
