import app.content.instructions as instructions


def test_seeds_template_on_first_use(tmp_path, monkeypatch):
    path = tmp_path / "instructions.md"
    monkeypatch.setattr(instructions, "INSTRUCTIONS_PATH", path)
    text = instructions.standing_instructions()
    assert path.exists()
    assert "standing instructions" in text.lower()


def test_returns_user_edits(tmp_path, monkeypatch):
    path = tmp_path / "instructions.md"
    path.write_text("- Always answer in Tamil.\n")
    monkeypatch.setattr(instructions, "INSTRUCTIONS_PATH", path)
    assert instructions.standing_instructions() == "- Always answer in Tamil."


def test_empty_file_returns_empty(tmp_path, monkeypatch):
    path = tmp_path / "instructions.md"
    path.write_text("   \n")
    monkeypatch.setattr(instructions, "INSTRUCTIONS_PATH", path)
    assert instructions.standing_instructions() == ""
