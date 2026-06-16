import json

import app.services.hooks as hooks


def _config(tmp_path, monkeypatch, data):
    path = tmp_path / "hooks.json"
    path.write_text(json.dumps(data))
    monkeypatch.setattr(hooks, "HOOKS_PATH", path)


def test_missing_config_created_and_allows_everything(tmp_path, monkeypatch):
    monkeypatch.setattr(hooks, "HOOKS_PATH", tmp_path / "hooks.json")
    assert hooks.pre_tool("run_command", {"command": "rm -rf /"}) is None
    assert (tmp_path / "hooks.json").exists()


def test_deny_hook_blocks_matching_call(tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, {
        "pre_tool": [{
            "tool": "run_command",
            "deny_if_contains": ["rm -rf"],
            "message": "blocked by test hook",
        }]
    })
    assert hooks.pre_tool("run_command", {"command": "rm -rf /tmp/x"}) == "blocked by test hook"
    assert hooks.pre_tool("run_command", {"command": "pytest -q"}) is None
    # other tools unaffected
    assert hooks.pre_tool("run_python", {"code": "rm -rf"}) is None


def test_star_matches_every_tool(tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, {
        "pre_tool": [{"tool": "*", "deny_if_contains": ["secret.txt"]}]
    })
    blocked = hooks.pre_tool("read_file", {"path": "/home/me/secret.txt"})
    assert blocked is not None and "hook" in blocked.lower()


def test_match_is_case_insensitive(tmp_path, monkeypatch):
    _config(tmp_path, monkeypatch, {
        "pre_tool": [{"tool": "run_command", "deny_if_contains": ["FORMAT C:"]}]
    })
    assert hooks.pre_tool("run_command", {"command": "format c: /y"}) is not None


def test_malformed_config_fails_open_with_warning(tmp_path, monkeypatch):
    path = tmp_path / "hooks.json"
    path.write_text("{not json")
    monkeypatch.setattr(hooks, "HOOKS_PATH", path)
    assert hooks.pre_tool("run_command", {"command": "anything"}) is None
