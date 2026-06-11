from app.history import COMPACT_MARKER, _clean, compact_history


def _msg(role, content):
    return {"role": role, "content": content}


def test_clean_drops_everything_before_marker():
    history = [
        _msg("user", "old 1"),
        _msg("assistant", "old reply"),
        _msg("assistant", COMPACT_MARKER + " summary here"),
        _msg("user", "new"),
        _msg("assistant", "new reply"),
    ]
    cleaned = _clean(history)
    assert len(cleaned) == 3
    assert cleaned[0]["content"].startswith(COMPACT_MARKER)


def test_clean_uses_most_recent_marker():
    history = [
        _msg("assistant", COMPACT_MARKER + " first"),
        _msg("user", "middle"),
        _msg("assistant", COMPACT_MARKER + " second"),
        _msg("user", "after"),
    ]
    cleaned = _clean(history)
    assert len(cleaned) == 2
    assert "second" in cleaned[0]["content"]


def test_clean_filters_non_text_entries():
    history = [
        _msg("user", "ok"),
        {"role": "user", "content": ("file.png",)},  # gradio file tuple
        {"role": "system", "content": "ignored"},
    ]
    assert _clean(history) == [_msg("user", "ok")]


def test_compact_history_under_threshold_passthrough():
    history = [_msg("user", "hi"), _msg("assistant", "hello")]
    summary, messages = compact_history(history)
    assert summary is None
    assert len(messages) == 2
