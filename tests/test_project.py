import subprocess

from app import gittools, project, sandbox


def teardown_function():
    project.set_project_folder("")


def test_select_project_folder_changes_command_root(tmp_path):
    selected = tmp_path / "selected"
    selected.mkdir()
    assert project.set_project_folder(str(selected))[0]

    out = sandbox.run_command("python -c \"import os; print(os.getcwd())\"", cwd=".")
    assert "succeeded" in out
    assert "selected" in out


def test_invalid_project_folder_is_rejected(tmp_path):
    ok, message = project.set_project_folder(str(tmp_path / "missing"))
    assert not ok
    assert "does not exist" in message


def test_git_tools_can_target_selected_project(tmp_path, monkeypatch):
    empty = tmp_path / "empty-gitconfig"
    empty.touch()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty))

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "file.txt").write_text("hello\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        [
            "git", "-C", str(repo), "-c", "user.name=t",
            "-c", "user.email=t@t", "commit", "-qm", "init",
        ],
        check=True,
    )
    project.set_project_folder(str(repo))

    status = gittools.git_status(".")
    assert "Branch: main" in status
