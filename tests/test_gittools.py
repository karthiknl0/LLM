import subprocess

import app.tools.git_ops as gittools


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(gittools, "REPOS_DIR", tmp_path)
    # hermetic git: ignore the host's global/system config (signing
    # hooks, default branch overrides, etc.)
    empty = tmp_path / "empty-gitconfig"
    empty.touch()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty))


def _make_repo(tmp_path, name="demo"):
    path = tmp_path / name
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    (path / "file.txt").write_text("hello\n")
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t",
         "commit", "-qm", "init"],
        check=True,
    )
    return path


def test_unknown_repo_handled(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert "No cloned repository" in gittools.git_status("ghost")
    assert "No cloned repository" in gittools.git_diff("ghost")
    assert "No cloned repository" in gittools.git_push("ghost")


def test_repo_name_path_tricks_rejected(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert gittools._resolve_repo("../escape") is None
    assert gittools._resolve_repo("a/b") is None


def test_commit_requires_ai_branch(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    _make_repo(tmp_path)
    reply = gittools.git_commit("demo", "main", "msg")
    assert "not allowed" in reply
    reply = gittools.git_commit("demo", "feature-x", "msg")
    assert "not allowed" in reply


def test_commit_on_ai_branch_works(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    path = _make_repo(tmp_path)
    (path / "file.txt").write_text("changed\n")
    reply = gittools.git_commit("demo", "ai/test-change", "change file")
    assert "Committed" in reply
    branch = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    assert branch == "ai/test-change"


def test_push_refused_on_protected_branch(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    _make_repo(tmp_path)  # repo sits on main
    assert "Refusing to push" in gittools.git_push("demo")


def test_diff_shows_changes(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    path = _make_repo(tmp_path)
    assert "(no uncommitted changes)" in gittools.git_diff("demo")
    (path / "file.txt").write_text("modified\n")
    diff = gittools.git_diff("demo")
    assert "+modified" in diff and "-hello" in diff
