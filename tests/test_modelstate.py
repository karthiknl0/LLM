import sys
from types import SimpleNamespace

import app.modelstate as modelstate
from app.config import CHAT_MODEL, EMBED_MODEL, VISION_MODEL


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
    monkeypatch.setitem(
        sys.modules,
        "ollama",
        SimpleNamespace(list=lambda: (_ for _ in ()).throw(RuntimeError("down"))),
    )
    names = modelstate.installed_models()
    assert "fallback-model" in names


def test_installed_models_excludes_specialized_models(monkeypatch):
    monkeypatch.setattr(modelstate, "_current", "deleted-model:14b")
    monkeypatch.setitem(
        sys.modules,
        "ollama",
        SimpleNamespace(
            list=lambda: {
                "models": [
                    {"model": "qwen3:8b"},
                    {"model": VISION_MODEL},
                    {"model": EMBED_MODEL + ":latest"},
                ]
            }
        ),
    )

    assert modelstate.installed_models() == ["qwen3:8b"]
