"""Loops: run a prompt or slash command on a recurring interval, like
Claude Code's /loop. Examples (in Chat or Agent):

    /loop 30 research the latest qwen model releases and note anything new
    /loop 60 /status
    /loops              — list running loops
    /stoploop a1b2c3    — stop one

Each loop runs in a background thread while the app is open (loops do
not survive a restart) and appends every run to data/loops/<id>.md.
Prompts run through the full tool-using agent; slash commands run
directly. Runs share the GPU with your chats — Ollama queues them.
"""

import datetime
import threading
import time
import uuid

from app.config import ROOT

LOOPS_DIR = ROOT / "data" / "loops"
MIN_INTERVAL_MINUTES = 1
MAX_LAST_CHARS = 1200

_loops: dict[str, dict] = {}


def _execute(prompt: str) -> str:
    from app.commands import handle_command

    command_reply = handle_command(prompt)
    if command_reply is not None:
        return command_reply
    from app.agent import SYSTEM_PROMPT, run_with_tools

    return run_with_tools(SYSTEM_PROMPT, prompt)


def _runner(loop_id: str) -> None:
    info = _loops[loop_id]
    LOOPS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOOPS_DIR / f"{loop_id}.md"
    while info["active"]:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            result = _execute(info["prompt"])
        except Exception as exc:
            result = f"(loop error: {exc})"
        info["runs"] += 1
        info["last"] = f"[{stamp}] {result[:MAX_LAST_CHARS]}"
        try:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"\n## {stamp}\n\n{result}\n")
        except OSError as exc:
            print(f"[loop {loop_id}] log failed: {exc}")
        # sleep in 1s steps so /stoploop takes effect quickly
        for _ in range(int(info["minutes"] * 60)):
            if not info["active"]:
                break
            time.sleep(1)


def start_loop(minutes: float, prompt: str) -> str:
    if not (prompt or "").strip():
        return "Usage: /loop <minutes> <prompt or /command>"
    if minutes < MIN_INTERVAL_MINUTES:
        return f"Minimum interval is {MIN_INTERVAL_MINUTES} minute(s)."
    loop_id = uuid.uuid4().hex[:6]
    _loops[loop_id] = {
        "prompt": prompt.strip(),
        "minutes": minutes,
        "active": True,
        "runs": 0,
        "last": "(not run yet)",
    }
    threading.Thread(target=_runner, args=(loop_id,), daemon=True).start()
    return (
        f"Loop `{loop_id}` started — every {minutes:g} min: {prompt.strip()}\n"
        f"Runs log to data/loops/{loop_id}.md · `/loops` to check · "
        f"`/stoploop {loop_id}` to stop."
    )


def stop_loop(loop_id: str) -> str:
    info = _loops.get((loop_id or "").strip())
    if not info or not info["active"]:
        return "No running loop with that ID — see /loops."
    info["active"] = False
    return f"Loop `{loop_id}` stopped after {info['runs']} run(s)."


def list_loops() -> str:
    active = {k: v for k, v in _loops.items() if v["active"]}
    if not active:
        return "No loops running. Start one: /loop <minutes> <prompt>"
    lines = []
    for loop_id, info in active.items():
        lines.append(
            f"- `{loop_id}` · every {info['minutes']:g} min · "
            f"{info['runs']} run(s) · {info['prompt'][:60]}\n"
            f"  last: {info['last'][:160]}"
        )
    return "**Running loops**\n" + "\n".join(lines)
