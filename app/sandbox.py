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
from app.project import active_project_folder

TIMEOUT_SECONDS = 60
COMMAND_TIMEOUT_SECONDS = 600   # builds and test suites can be slow
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
    root = active_project_folder(WORKSPACE_DIR)
    before = {p.name for p in root.iterdir()}

    try:
        proc = subprocess.run(
            [sys.executable, "-I", str(script)],
            cwd=root,
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
        {p.name for p in root.iterdir()} - before - {script.name}
    )
    if new_files:
        output += f"\n\nFiles created in {root}: " + ", ".join(new_files)
    return output


def _resolve_cwd(cwd: str):
    """A working directory inside the selected project, or None if it escapes."""
    base = active_project_folder(WORKSPACE_DIR).resolve()
    target = (base / (cwd or "")).resolve()
    if target != base and base not in target.parents:
        return None
    return target if target.is_dir() else None


def run_command(command: str, cwd: str = "") -> str:
    """Run a build/test/shell command inside the workspace (e.g. in a
    cloned repo under repos/<name>) and return its output and exit code.

    Honest note: like run_python, this executes on your machine with
    your account — confined to the workspace by directory, not a hard
    sandbox. Use it to build and test code the agent edits."""
    if not (command or "").strip():
        return "No command provided."
    target = _resolve_cwd(cwd)
    if target is None:
        return (
            f"Working directory '{cwd}' is outside the workspace/project folder "
            "or does not exist. Use a path under the selected project folder."
        )
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=target,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {COMMAND_TIMEOUT_SECONDS} seconds."

    output = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    output = output.strip() or "(no output)"
    if len(output) > MAX_OUTPUT_CHARS:
        output = "... (earlier output truncated)\n" + output[-MAX_OUTPUT_CHARS:]
    status = "succeeded" if proc.returncode == 0 else f"failed (exit {proc.returncode})"
    return f"Command {status}.\n\n{output}"
