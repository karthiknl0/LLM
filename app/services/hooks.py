"""Lifecycle hooks, like Claude Code's: your own rules and commands
that run when things happen — enforced in code, so the model can't
talk its way around them. Configure in data/hooks.json:

    {
      "session_start": [
        {"command": "echo hub started >> hub.log"}
      ],
      "pre_tool": [
        {"tool": "run_command",
         "deny_if_contains": ["rm -rf", "del /f", "format "],
         "message": "Blocked by your hook: destructive command."},
        {"tool": "*", "command": "echo tool used >> hub.log"}
      ],
      "post_reply": [
        {"command": "notify-send 'Local AI Hub replied'"}
      ]
    }

pre_tool hooks with "deny_if_contains" block the tool call when any
needle appears in the tool name or arguments; hooks with "command"
just run it (observability). "tool" matches a tool name or "*".
"""

import json
import os
import subprocess

from app.core.config import ROOT

HOOKS_PATH = ROOT / "data" / "hooks.json"
COMMAND_TIMEOUT = 10

_DEFAULT = '{\n  "session_start": [],\n  "pre_tool": [],\n  "post_reply": []\n}\n'


def _load() -> dict:
    if not HOOKS_PATH.exists():
        HOOKS_PATH.write_text(_DEFAULT, encoding="utf-8")
        return {}
    try:
        return json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[hooks] bad {HOOKS_PATH.name}: {exc}")
        return {}


def _run(command: str, extra_env: dict | None = None) -> None:
    try:
        subprocess.run(
            command, shell=True, timeout=COMMAND_TIMEOUT,
            capture_output=True, env={**os.environ, **(extra_env or {})},
        )
    except Exception as exc:
        print(f"[hooks] command failed: {exc}")


def pre_tool(tool_name: str, arguments: dict) -> str | None:
    """A block message if a hook denies this tool call, else None."""
    haystack = f"{tool_name} {json.dumps(arguments, ensure_ascii=False)}".lower()
    for hook in _load().get("pre_tool", []):
        if hook.get("tool") not in ("*", tool_name):
            continue
        needles = hook.get("deny_if_contains") or []
        if needles:
            if any(str(n).lower() in haystack for n in needles):
                return hook.get(
                    "message", "Blocked by one of your pre_tool hooks."
                )
        elif hook.get("command"):
            _run(hook["command"], {"HUB_TOOL": tool_name})
    return None


def post_reply(reply: str) -> None:
    for hook in _load().get("post_reply", []):
        if hook.get("command"):
            _run(hook["command"], {"HUB_REPLY": (reply or "")[:500]})


def session_start() -> None:
    for hook in _load().get("session_start", []):
        if hook.get("command"):
            _run(hook["command"])
