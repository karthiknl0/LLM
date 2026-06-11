import app.playbooks as playbooks


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(playbooks, "PLAYBOOKS_DIR", tmp_path)


def test_seeds_on_first_use(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    names = [name for name, _desc in playbooks.catalog()]
    assert "debug-a-failing-test" in names
    assert "security-review" in names
    assert len(names) == len(playbooks.SEED)


def test_seed_does_not_overwrite_user_edits(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    custom = tmp_path / "mine.md"
    custom.write_text("---\nname: mine\ndescription: my flow\n---\nbody\n")
    names = [name for name, _desc in playbooks.catalog()]
    assert names == ["mine"]  # seeding skipped because dir non-empty


def test_load_playbook_returns_body(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    playbooks.catalog()  # trigger seed
    body = playbooks.load_playbook("debug-a-failing-test")
    assert "## Workflow" in body


def test_load_playbook_unknown_lists_available(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    playbooks.catalog()
    reply = playbooks.load_playbook("nope")
    assert "No playbook" in reply and "debug-a-failing-test" in reply


def test_load_playbook_sanitizes_path_tricks(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    playbooks.catalog()
    reply = playbooks.load_playbook("../../etc/passwd")
    assert "No playbook" in reply


def test_catalog_hint_lists_descriptions(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    hint = playbooks.catalog_hint()
    assert "load_playbook" in hint and "debug-a-failing-test" in hint
