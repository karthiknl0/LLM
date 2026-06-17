import app.session.modelstate as modelstate
from app.core.config import CHAT_MODEL


def test_defaults_to_config(monkeypatch):
    monkeypatch.setattr(modelstate, "_current", CHAT_MODEL)
    assert modelstate.current_model() == CHAT_MODEL


def test_set_and_get_roundtrip(monkeypatch):
    monkeypatch.setattr(modelstate, "_current", CHAT_MODEL)
    reply = modelstate.set_model("deepseek-r1:14b")
    assert "deepseek-r1:14b" in reply
    assert modelstate.current_model() == "deepseek-r1:14b"


def test_blank_name_keeps_current(monkeypatch):
    monkeypatch.setattr(modelstate, "_current", "keep-me")
    modelstate.set_model("   ")
    assert modelstate.current_model() == "keep-me"


def test_installed_models_falls_back_when_ollama_down(monkeypatch):
    monkeypatch.setattr(modelstate, "_current", "fallback-model")
    names = modelstate.installed_models()  # no ollama server in tests
    assert "fallback-model" in names
