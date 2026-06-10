"""Python execution for the agent: lets the model compute instead of
guess (math, data analysis, plots, file processing).

Code runs in a subprocess confined to data/workspace/ with a timeout.
Honest note: this is your own machine, not a hardened sandbox — the
agent's code runs with your user account. It is only invoked from the
Agent tab, and everything it does is visible in the reply.
"""

import shutil
import subprocess
import sys

from app.config import SKILLS_DIR, WORKSPACE_DIR

TIMEOUT_SECONDS = 60
MAX_OUTPUT_CHARS = 4000


def _sync_skills() -> None:
    """Copy saved skills into the workspace as a `skills` package so
    agent code can `from skills.<name> import <name>`."""
    try:
        package = WORKSPACE_DIR / "skills"
        package.mkdir(exist_ok=True)
        (package / "__init__.py").touch()
        for source in SKILLS_DIR.glob("*.py"):
            shutil.copy(source, package / source.name)
    except Exception as exc:
        print(f"[sandbox] skill sync failed: {exc}")


def run_python(code: str) -> str:
    """Run a Python snippet in the workspace; return its output and any
    files it created."""
    if not code.strip():
        return "No code provided."
    _sync_skills()

    script = WORKSPACE_DIR / "_agent_script.py"
    script.write_text(code, encoding="utf-8")
    before = {p.name for p in WORKSPACE_DIR.iterdir()}

    try:
        proc = subprocess.run(
            [sys.executable, "-I", script.name],
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        output = proc.stdout
        if proc.stderr:
            output += ("\n" if output else "") + proc.stderr
        output = output.strip() or "(no output — use print() to show results)"
    except subprocess.TimeoutExpired:
        return f"Execution timed out after {TIMEOUT_SECONDS} seconds."

    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n... (output truncated)"

    new_files = sorted(
        {p.name for p in WORKSPACE_DIR.iterdir()} - before - {script.name}
    )
    if new_files:
        output += "\n\nFiles created in data/workspace/: " + ", ".join(new_files)
    return output
