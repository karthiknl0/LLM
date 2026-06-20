"""Guarded git tools for the agent: clone, status, commit, push.

The guardrails live in code, not in the prompt, so a confused model
cannot bypass them:
- all work happens inside data/workspace/repos/
- commits only land on branches named ai/<something>
- pushing main/master is impossible; force-push does not exist here
- you merge via pull request on GitHub — the agent only proposes

Pushes authenticate with the AIHUB_GITHUB_TOKEN env var if set (use a
fine-grained PAT scoped to only the repos you choose, Contents:write).
Otherwise whatever git credential helper you already use applies.
"""

import os
import re
import subprocess

from app.config import WORKSPACE_DIR
from app.project import active_project_folder

REPOS_DIR = WORKSPACE_DIR / "repos"
BRANCH_PATTERN = re.compile(r"ai/[A-Za-z0-9._-]+")
SAFE_NAME = re.compile(r"[A-Za-z0-9._-]+")
PROTECTED_BRANCHES = {"main", "master"}


def _git(repo_path, *args, timeout: int = 120) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError:
        return False, "git is not installed"
    except subprocess.TimeoutExpired:
        return False, "git timed out"


def _resolve_repo(name: str):
    """Repo directory inside the workspace or selected project, or None."""
    if (name or "").strip().lower() in {".", "current", "project"}:
        path = active_project_folder()
        return path if (path / ".git").exists() else None
    if not name or not SAFE_NAME.fullmatch(name):
        return None
    path = REPOS_DIR / name
    return path if (path / ".git").exists() else None


def git_clone(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return "Provide a repository URL."
    name = re.sub(r"\.git$", "", url.rstrip("/").split("/")[-1])
    if not SAFE_NAME.fullmatch(name):
        return "Could not derive a safe repository name from that URL."
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    destination = REPOS_DIR / name
    if destination.exists():
        return f"'{name}' is already cloned — check it with git_status."
    try:
        proc = subprocess.run(
            ["git", "clone", url, str(destination)],
            capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        return "git is not installed."
    except subprocess.TimeoutExpired:
        return "git clone timed out."
    if proc.returncode != 0:
        return f"Clone failed: {proc.stderr.strip()[:500]}"
    return (
        f"Cloned '{name}'. Its files live under 'repos/{name}/' in the "
        "workspace — read and edit them with run_python."
    )


def git_status(repo: str) -> str:
    path = _resolve_repo(repo)
    if not path:
        return f"No cloned repository named '{repo}' — use git_clone first."
    _ok, branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD")
    _ok, changes = _git(path, "status", "--short")
    _ok, diffstat = _git(path, "diff", "--stat")
    return (
        f"Branch: {branch}\n"
        f"Changes:\n{changes or '(working tree clean)'}\n"
        f"{diffstat}".strip()
    )


def git_diff(repo: str) -> str:
    """Full diff of uncommitted (and staged) changes in a cloned repo."""
    path = _resolve_repo(repo)
    if not path:
        return f"No cloned repository named '{repo}' — use git_clone first."
    _ok, unstaged = _git(path, "diff")
    _ok, staged = _git(path, "diff", "--cached")
    combined = "\n".join(part for part in (staged, unstaged) if part).strip()
    if not combined:
        return "(no uncommitted changes)"
    if len(combined) > 6000:
        combined = combined[:6000] + "\n... (diff truncated)"
    return combined


def git_commit(repo: str, branch: str, message: str) -> str:
    path = _resolve_repo(repo)
    if not path:
        return f"No cloned repository named '{repo}' — use git_clone first."
    if not branch or not BRANCH_PATTERN.fullmatch(branch):
        return (
            "Branch must look like ai/short-description — committing to "
            "other branches is not allowed."
        )
    if not (message or "").strip():
        return "Provide a commit message."

    ok, output = _git(path, "checkout", "-B", branch)
    if not ok:
        return f"Could not switch to {branch}: {output[:300]}"
    _git(path, "add", "-A")

    identity = []
    if not _git(path, "config", "user.email")[1].strip():
        identity = ["-c", "user.name=Local AI Hub", "-c", "user.email=ai@localhost"]
    ok, output = _git(path, *identity, "commit", "-m", message.strip())
    if not ok:
        return f"Nothing committed: {output[:300]}"
    return f"Committed to branch '{branch}'. Push with git_push when the user asks."


def git_push(repo: str) -> str:
    path = _resolve_repo(repo)
    if not path:
        return f"No cloned repository named '{repo}' — use git_clone first."
    _ok, branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch.strip()
    if branch in PROTECTED_BRANCHES or not BRANCH_PATTERN.fullmatch(branch):
        return (
            f"Refusing to push '{branch}' — only ai/* branches can be "
            "pushed. Commit with git_commit first."
        )

    token = os.environ.get("AIHUB_GITHUB_TOKEN")
    if token:
        _ok, origin = _git(path, "config", "--get", "remote.origin.url")
        origin = origin.strip()
        if origin.startswith("https://"):
            authed = origin.replace("https://", f"https://x-access-token:{token}@", 1)
            ok, output = _git(
                path, "push", authed, f"HEAD:refs/heads/{branch}", timeout=300
            )
        else:
            ok, output = _git(path, "push", "-u", "origin", branch, timeout=300)
        output = output.replace(token, "***")
    else:
        ok, output = _git(path, "push", "-u", "origin", branch, timeout=300)

    if not ok:
        return f"Push failed: {output[:500]}"
    return (
        f"Pushed branch '{branch}'. Open a pull request on GitHub to "
        "review and merge it."
    )
