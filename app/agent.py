"""Agent mode: one chat where the model decides for itself when to
search your documents, research the web, or generate an image — using
Ollama's native tool calling. Fully local routing.
"""

from app import imagegen, rag, research, sandbox
from app.chat import _log_turn
from app.config import CHAT_MODEL
from app.memory import recall, recall_lessons, remember

import ollama

MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = (
    "You are a helpful local AI assistant running entirely on the user's "
    "own computer, with tools. Use search_documents for questions about "
    "the user's own files, web_research for current events or anything "
    "you're unsure about, generate_image when asked to create a picture, "
    "and run_python for any calculation, data analysis, or file "
    "processing — never do arithmetic in your head. Answer directly from "
    "your own knowledge when no tool is needed. Be concise and practical."
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
}

TOOL_STATUS = {
    "search_documents": "Searching your documents",
    "web_research": "Researching the web",
    "generate_image": "Generating image",
    "run_python": "Running Python code",
}


def agent_chat(message: str, history: list[dict], deep_answer: bool = False):
    """Generator for the Agent tab: yields tool-use progress, then the
    final answer. With deep_answer, the model reviews and corrects its
    own draft before replying (slower, more reliable)."""
    system = SYSTEM_PROMPT
    memories = recall(message)
    if memories:
        system += "\n\nThings you remember about the user:\n"
        system += "\n".join(f"- {m}" for m in memories)
    lessons = recall_lessons(message)
    if lessons:
        system += "\n\nStanding instructions learned from past corrections:\n"
        system += "\n".join(f"- {lesson}" for lesson in lessons)

    messages = [{"role": "system", "content": system}]
    messages += [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)
    ]
    messages.append({"role": "user", "content": message})

    steps = []
    reply = "(no answer)"
    for _round in range(MAX_TOOL_ROUNDS + 1):
        response = ollama.chat(model=CHAT_MODEL, messages=messages, tools=TOOLS)
        msg = response["message"]
        tool_calls = getattr(msg, "tool_calls", None) or []

        if not tool_calls or _round == MAX_TOOL_ROUNDS:
            reply = msg["content"]
            break

        messages.append(msg)
        for call in tool_calls:
            name = call["function"]["name"]
            arguments = dict(call["function"]["arguments"] or {})
            steps.append(f"*{TOOL_STATUS.get(name, name)}…*")
            yield "\n\n".join(steps)
            try:
                result = TOOL_FUNCTIONS[name](**arguments)
            except Exception as exc:
                result = f"Tool failed: {exc}"
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
