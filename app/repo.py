"""Chat with any codebase: clone a GitHub repository (shallow) into
data/documents/repos/ and index it with the existing RAG pipeline.
Cloning is the only network step — the analysis stays on your machine.
"""

import re
import subprocess

from app.config import DOCUMENTS_DIR
from app.rag import index_documents

REPOS_DIR = DOCUMENTS_DIR / "repos"


def add_repo(url: str) -> str:
    """Clone (or update) a repository, then rebuild the document index."""
    url = url.strip()
    if not url:
        return "Paste a repository URL first."
    name = re.sub(r"\.git$", "", url.rstrip("/").split("/")[-1]) or "repo"
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    destination = REPOS_DIR / name

    try:
        if destination.exists():
            subprocess.run(
                ["git", "-C", str(destination), "pull", "--ff-only"],
                check=True, capture_output=True, text=True, timeout=300,
            )
            action = "Updated"
        else:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(destination)],
                check=True, capture_output=True, text=True, timeout=600,
            )
            action = "Cloned"
    except FileNotFoundError:
        return "git is not installed — install git to add repositories."
    except subprocess.TimeoutExpired:
        return "git timed out — very large repo or slow network?"
    except subprocess.CalledProcessError as exc:
        return f"git failed: {(exc.stderr or str(exc)).strip()[:500]}"

    return f"{action} `{name}`. {index_documents()}"
