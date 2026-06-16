import app.tools.file_ops as fileedit


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(fileedit, "EDIT_ROOTS", [tmp_path / "allowed"])
    monkeypatch.setattr(fileedit, "BACKUPS_DIR", tmp_path / "backups")
    (tmp_path / "allowed").mkdir()
    (tmp_path / "backups").mkdir()
    fileedit._pending.clear()


def test_read_outside_scope_refused(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    assert "outside the allowed folders" in fileedit.read_file(str(outside))


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
