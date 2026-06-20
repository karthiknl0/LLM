import app.tools.code_exec as sandbox


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "WORKSPACE_DIR", tmp_path)
    monkeypatch.setattr(sandbox, "SKILLS_DIR", tmp_path / "no-skills")


def test_run_python_executes_and_reports_files(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    out = sandbox.run_python("print(2 + 3)\nopen('made.txt', 'w').write('x')")
    assert "5" in out
    assert "made.txt" in out


def test_run_python_surfaces_errors(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    out = sandbox.run_python("1 / 0")
    assert "ZeroDivisionError" in out


def test_run_command_in_workspace(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    out = sandbox.run_command("echo hello-hub")
    assert "succeeded" in out and "hello-hub" in out


def test_run_command_reports_failure_exit_code(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    out = sandbox.run_command("exit 3")
    assert "failed (exit 3)" in out


def test_run_command_cwd_cannot_escape(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    out = sandbox.run_command("echo nope", cwd="../..")
    assert "outside the selected project" in out


def test_run_command_cwd_inside_workspace(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    (tmp_path / "sub").mkdir()
    out = sandbox.run_command("pwd", cwd="sub")
    assert "succeeded" in out and "sub" in out
