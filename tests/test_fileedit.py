import app.tools.file_ops as fileedit
from app.core import project


def teardown_function():
    project.set_project_folder("")


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(fileedit, "EDIT_ROOTS", [tmp_path / "allowed"])
    monkeypatch.setattr(fileedit, "BACKUPS_DIR", tmp_path / "backups")
    (tmp_path / "allowed").mkdir()
    (tmp_path / "backups").mkdir()
    project.set_project_folder(str(tmp_path / "allowed"))
    fileedit._pending.clear()


def test_read_outside_scope_refused(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    assert "outside the allowed folders" in fileedit.read_file(str(outside))


def test_list_files_and_search_content(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    root = tmp_path / "allowed"
    (root / "app").mkdir()
    (root / "app" / "agent.py").write_text("def agent_chat():\n    return 'ok'\n")
    (root / ".git").mkdir()
    (root / ".git" / "ignored").write_text("agent_chat")

    listing = fileedit.list_files(str(root), depth=2)
    assert "app/" in listing
    assert "agent.py" in listing
    assert ".git" not in listing

    results = fileedit.search_files("agent_chat", str(root))
    assert "agent.py:1" in results
    assert "ignored" not in results


def test_propose_approve_applies_with_backup(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    target = tmp_path / "allowed" / "note.txt"
    target.write_text("old content\n")

    reply = fileedit.propose_edit(str(target), "new content\n", "test")
    assert "queued" in reply and "approve" in reply.lower()
    assert target.read_text() == "old content\n"  # nothing written yet

    edit_id = fileedit.list_pending()[0][0]
    assert "-old content" in fileedit.show_diff(edit_id)
    assert "+new content" in fileedit.show_diff(edit_id)

    result = fileedit.approve(edit_id)
    assert "Applied" in result
    assert target.read_text() == "new content\n"
    assert list((tmp_path / "backups").glob("note.txt.*.bak"))
    assert fileedit.list_pending() == []


def test_reject_discards(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    target = tmp_path / "allowed" / "a.txt"
    target.write_text("x")
    fileedit.propose_edit(str(target), "y", "")
    edit_id = fileedit.list_pending()[0][0]
    assert "rejected" in fileedit.reject(edit_id).lower()
    assert target.read_text() == "x"
    assert fileedit.list_pending() == []


def test_identical_content_not_queued(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    target = tmp_path / "allowed" / "same.txt"
    target.write_text("same")
    reply = fileedit.propose_edit(str(target), "same", "")
    assert "identical" in reply
    assert fileedit.list_pending() == []


def test_approve_unknown_id(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert "No pending edit" in fileedit.approve("nope")


def test_relative_paths_resolve_from_active_project(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    root = tmp_path / "allowed"
    (root / "requirements.txt").write_text("old\n")

    assert fileedit.read_file("requirements.txt") == "old\n"
    result = fileedit.write_file("requirements.txt", "new\n")
    assert "Wrote" in result
    assert (root / "requirements.txt").read_text() == "new\n"
    assert list((tmp_path / "backups").glob("requirements.txt.*.bak"))


def test_write_file_creates_project_file_and_blocks_escape(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    root = tmp_path / "allowed"

    result = fileedit.write_file("config/new.txt", "created\n")
    assert "Wrote" in result
    assert (root / "config" / "new.txt").read_text() == "created\n"

    outside = tmp_path / "outside.txt"
    refused = fileedit.write_file(str(outside), "nope")
    assert "outside the active project" in refused
    assert not outside.exists()

def test_edit_file_replaces_one_exact_block(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    root = tmp_path / "allowed"
    target = root / "app.py"
    target.write_text("before\nold block\nafter\n")

    result = fileedit.edit_file("app.py", "old block", "new block")
    assert "Edited" in result
    assert target.read_text() == "before\nnew block\nafter\n"

    target.write_text("same\nsame\n")
    refused = fileedit.edit_file("app.py", "same", "changed")
    assert "matches 2 places" in refused
    assert target.read_text() == "same\nsame\n"
