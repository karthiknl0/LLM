from app.local_code import editing, indexer


def test_project_index_build_and_search(tmp_path, monkeypatch):
    project = tmp_path / "repo"
    project.mkdir()
    (project / "app.py").write_text("def choose_runtime():\n    return 'ollama'\n", encoding="utf-8")
    (project / "image.png").write_text("skip", encoding="utf-8")
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    monkeypatch.setattr(indexer, "LOCAL_CODE_INDEX_DIR", index_dir)

    data = indexer.build_project_index(project)
    matches = indexer.search_project_index(project, "choose runtime")

    assert len(data["files"]) == 1
    assert matches[0].path == "app.py"
    assert "choose_runtime" in matches[0].snippet


def test_edit_queue_apply_and_backup(tmp_path, monkeypatch):
    project = tmp_path / "repo"
    project.mkdir()
    target = project / "app.py"
    target.write_text("old\n", encoding="utf-8")
    edits_dir = tmp_path / "edits"
    backups_dir = tmp_path / "backups"
    edits_dir.mkdir()
    backups_dir.mkdir()
    monkeypatch.setattr(editing, "LOCAL_CODE_EDITS_DIR", edits_dir)
    monkeypatch.setattr(editing, "BACKUPS_DIR", backups_dir)

    edit = editing.propose_file(project, "app.py", "new\n", reason="test")

    assert edit.id
    assert "-old" in editing.show_edit(edit.id)
    assert editing.list_edits()[0].id == edit.id
    result = editing.apply_edit(edit.id)

    assert "Applied edit" in result
    assert target.read_text(encoding="utf-8") == "new\n"
    assert list(backups_dir.glob("app.py.*.bak"))
