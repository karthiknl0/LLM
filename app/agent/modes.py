"""Agent operating modes and associated constants."""

MAX_TOOL_ROUNDS = 6
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

# Plan mode: only these tools are available — inspection, no changes.
# (git_clone is allowed: exploring a repo requires having it locally.)
READ_ONLY_TOOLS = {
    "search_documents", "web_research", "read_file", "list_files",
    "search_files", "git_clone",
    "git_status", "look_at_screen", "verify_in_browser", "read_notes",
    "load_playbook", "search_email", "read_email",
}

PLAN_MODE_PROMPT = (
    "\n\nPLAN MODE IS ON. You may only inspect: read files, search, "
    "research — your editing and execution tools are disabled. Do NOT "
    "attempt changes. Deliverable: a numbered implementation plan — for "
    "each step, what you'll change and how you'll verify it (test "
    "command, browser check). State assumptions and open questions. End "
    "by telling the user to untick Plan mode and say 'execute the plan' "
    "when they approve."
)
