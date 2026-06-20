"""Tool registry: JSON schemas for every agent tool, the dispatch table
that maps names to callables, and helpers to merge in MCP server tools.
"""

from app.core.config import ROOT
from app.media.imagegen import generate_image as _raw_generate_image
from app.services import mcp
from app.tools.code_exec import run_command, run_python
from app.tools.file_ops import edit_file, list_files, propose_edit, read_file, search_files, write_file
from app.tools.git_ops import git_clone, git_commit, git_pull, git_push, git_status
from app.tools.browser import verify_in_browser
from app.tools.screen import look_at_screen
from app.services.mail import read_email, search_email
from app.content.notes import read_notes, take_note
from app.content.playbooks import load_playbook
from app.rag import retrieve_context
from app.services.research import research as _research_fn


def _run_search_documents(query: str) -> str:
    retrieved = retrieve_context(query)
    if retrieved is None:
        return "No indexed documents (or nothing relevant). The user can add files to data/documents/ and index them in the Documents tab."
    context, _sources = retrieved
    return context


def _run_web_research(query: str) -> str:
    return _research_fn(query)


def _run_generate_image(prompt: str) -> str:
    _image, status = _raw_generate_image(prompt)
    return f"Image generated. {status} Tell the user where it was saved."


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
                "is the active project folder selected by the user. Read "
                "and write files there, print() results, and save plots as "
                ".png files. pandas and matplotlib are available."
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
                "Read a file. Relative paths such as 'requirements.txt' are "
                "resolved from the active project root; absolute paths in "
                "the user's allowed folders also work."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Project-relative or absolute file path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                f"List files and folders. Use path '{ROOT}' for your own "
                "Local AI Hub source code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute folder path"},
                    "depth": {"type": "integer", "description": "Depth from 1 to 5"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": (
                f"Search filenames and file content. Use path '{ROOT}' "
                "to search your own Local AI Hub source code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text to find"},
                    "path": {"type": "string", "description": "Absolute folder path"},
                },
                "required": ["query", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Edit an existing active-project file by replacing one exact, "
                "unique text block. Read the file first, then pass the exact "
                "old_text and its replacement. Applied immediately with a "
                "backup. Prefer this over rewriting a whole source file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the active project",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Exact unique text currently in the file",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Replacement text",
                    },
                },
                "required": ["path", "old_text", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Create or replace a file directly inside the active project. "
                "Use a project-relative path and provide the COMPLETE content. "
                "The change is applied immediately and existing files are "
                "backed up automatically. Use this when the user asks you to "
                "implement, create, update, fix, or upgrade project files."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the active project",
                    },
                    "new_content": {
                        "type": "string",
                        "description": "Complete new file content",
                    },
                },
                "required": ["path", "new_content"],
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
                    "path": {"type": "string", "description": "Project-relative or absolute file path"},
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
                "Run a build, test, or shell command inside the active "
                "project and get its output and exit code. Set cwd to '.' "
                "for the project root. Use to build and test code you edit: "
                "pytest, npm test, npm run build, make, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "cwd": {
                        "type": "string",
                        "description": "Directory inside the project; use '.' for root",
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
            "description": "Show branch and changes. Use repo='.' for the active project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Use '.' for active project"}
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
                "Commit project changes. Use repo='.' for the active project. "
                "The branch must be named ai/<short-description>."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Use '.' for active project"},
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
                "Push the current ai/ branch of a repository so the "
                "user can open a pull request. Only use when the user "
                "explicitly asks to push."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Use '.' for active project"}
                },
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_pull",
            "description": "Pull latest commits into an existing local git repo at an absolute path (e.g. C:/Users/me/my-project). Fast-forward only; never discards local work. Use when asked to pull or update a repo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the git repo"},
                    "remote": {"type": "string", "description": "Remote, default origin"},
                    "branch": {"type": "string", "description": "Branch to pull, e.g. main"},
                },
                "required": ["path"],
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
            "name": "search_email",
            "description": (
                "List the user's recent inbox emails (read-only), "
                "optionally filtered by a search term. Returns ids, "
                "subjects, senders, dates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional search term",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": (
                "Read one email by the numeric id from search_email "
                "(read-only — cannot send or delete)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "Numeric id from search_email",
                    }
                },
                "required": ["email_id"],
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

TOOL_FUNCTIONS = {
    "search_documents": _run_search_documents,
    "web_research": _run_web_research,
    "generate_image": _run_generate_image,
    "run_python": run_python,
    "look_at_screen": look_at_screen,
    "verify_in_browser": verify_in_browser,
    "search_email": search_email,
    "read_email": read_email,
    "take_note": take_note,
    "read_notes": read_notes,
    "load_playbook": load_playbook,
    "run_command": run_command,
    "read_file": read_file,
    "list_files": list_files,
    "search_files": search_files,
    "edit_file": edit_file,
    "write_file": write_file,
    "propose_edit": propose_edit,
    "git_clone": git_clone,
    "git_status": git_status,
    "git_commit": git_commit,
    "git_push": git_push,
    "git_pull": git_pull,
}

TOOL_STATUS = {
    "search_documents": "Searching your documents",
    "web_research": "Researching the web",
    "generate_image": "Generating image",
    "run_python": "Running Python code",
    "look_at_screen": "Looking at your screen",
    "verify_in_browser": "Verifying in the browser",
    "search_email": "Searching your email (read-only)",
    "read_email": "Reading an email",
    "take_note": "Taking a note",
    "read_notes": "Reading notes",
    "load_playbook": "Loading a playbook",
    "run_command": "Building / running tests",
    "read_file": "Reading a file",
    "list_files": "Browsing project files",
    "search_files": "Searching project code",
    "edit_file": "Editing a project file",
    "write_file": "Writing a project file",
    "propose_edit": "Proposing a file edit (needs your approval)",
    "git_clone": "Cloning repository",
    "git_status": "Checking git status",
    "git_commit": "Committing changes",
    "git_push": "Pushing branch",
    "git_pull": "Pulling latest from git",
}


def all_tools() -> list[dict]:
    """Built-in tools plus any from configured MCP servers."""
    return TOOLS + mcp.mcp_tools()


def all_functions() -> dict:
    return {**TOOL_FUNCTIONS, **mcp.mcp_functions()}
