from app.commands import COMMANDS, export_chat, handle_command


def test_non_command_passes_through():
    assert handle_command("hello there") is None
    assert handle_command("") is None


def test_help_lists_every_command():
    reply = handle_command("/help")
    for name in COMMANDS:
        assert f"/{name}" in reply


def test_unknown_command_shows_help():
    reply = handle_command("/bogus")
    assert "Unknown command" in reply and "/help" in reply


def test_loop_rejects_bad_usage():
    assert "Usage" in handle_command("/loop notanumber do something")
    assert "Usage" in handle_command("/research")
    assert "Usage" in handle_command("/diff")


def test_playbook_requires_name():
    assert "Usage" in handle_command("/playbook")


def test_export_chat_writes_markdown(tmp_path, monkeypatch):
    import app.commands as commands_module
    import app.config as config

    monkeypatch.setattr(config, "OUTPUTS_DIR", tmp_path)
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    reply = export_chat(history)
    assert "exported" in reply
    files = list(tmp_path.glob("chat_*.md"))
    assert len(files) == 1
    text = files[0].read_text()
    assert "hello" in text and "hi" in text


def test_export_chat_empty():
    assert "Nothing to export" in export_chat([])
