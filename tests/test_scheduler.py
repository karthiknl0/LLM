import time

import app.scheduler as scheduler


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(scheduler, "LOOPS_DIR", tmp_path)
    scheduler._loops.clear()


def test_start_requires_prompt_and_sane_interval(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert "Usage" in scheduler.start_loop(5, "")
    assert "Minimum interval" in scheduler.start_loop(0.1, "do x")


def test_loop_lifecycle_with_command(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    # a slash command loop needs no LLM; /help is instant
    reply = scheduler.start_loop(1, "/help")
    assert "started" in reply
    loop_id = next(iter(scheduler._loops))

    # first run is immediate; give the thread a moment
    for _ in range(50):
        if scheduler._loops[loop_id]["runs"] >= 1:
            break
        time.sleep(0.1)
    assert scheduler._loops[loop_id]["runs"] >= 1
    assert "Commands" in scheduler._loops[loop_id]["last"]
    assert (tmp_path / f"{loop_id}.md").exists()

    listed = scheduler.list_loops()
    assert loop_id in listed

    assert "stopped" in scheduler.stop_loop(loop_id)
    assert "No loops running" in scheduler.list_loops()


def test_stop_unknown_loop(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert "No running loop" in scheduler.stop_loop("nope")
