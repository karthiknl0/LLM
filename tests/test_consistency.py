import app.consistency as consistency


def test_final_line_extracts_last():
    text = "step 1\nFINAL: 42\nmore\nFINAL: 391."
    assert consistency._final_line(text) == "391"


def test_final_line_strips_thinking_block():
    text = "<think>FINAL: wrong</think>\nFINAL: right"
    assert consistency._final_line(text) == "right"


def test_final_line_none_when_absent():
    assert consistency._final_line("no marker here") is None


def test_empty_question():
    assert "Ask a question" in consistency.self_consistency("")


def test_majority_vote(monkeypatch):
    # fake five samples: 42, 42, 42, 7, 42  -> majority 42 (4/5)
    replies = iter(["FINAL: 42", "FINAL: 42", "FINAL: 42", "FINAL: 7", "FINAL: 42"])

    def fake_chat(model, messages, options=None):
        return {"message": {"content": next(replies)}}

    monkeypatch.setattr(consistency.ollama, "chat", fake_chat)
    out = consistency.self_consistency("what is 6*7?", samples=5)
    assert "42" in out
    assert "4/5" in out


def test_handles_chat_failure(monkeypatch):
    def boom(model, messages, options=None):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(consistency.ollama, "chat", boom)
    assert "Voting failed" in consistency.self_consistency("q", samples=3)
