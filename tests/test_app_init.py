import app


def test_chat_wrapper_sets_generation_budgets(monkeypatch):
    captured = {}

    def fake_chat(*args, **kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(app, "_real_chat", fake_chat)
    assert app._chat_no_think(model="test", messages=[]) == "ok"
    assert captured["think"] is False
    assert captured["options"]["num_ctx"] == 32768
    assert captured["options"]["num_predict"] == 4096


def test_chat_wrapper_preserves_explicit_options(monkeypatch):
    captured = {}

    def fake_chat(*args, **kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(app, "_real_chat", fake_chat)
    app._chat_no_think(
        options={"num_ctx": 8192, "temperature": 0.2}, think=True
    )
    assert captured["think"] is True
    assert captured["options"] == {
        "num_ctx": 8192, "num_predict": 4096, "temperature": 0.2
    }
