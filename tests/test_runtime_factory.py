import importlib

import pytest


def test_runtime_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("AIHUB_RUNTIME", raising=False)
    import app.runtime.factory as factory

    importlib.reload(factory)

    assert factory.runtime().name == "ollama"


def test_runtime_recognizes_llamacpp_placeholder(monkeypatch):
    monkeypatch.setenv("AIHUB_RUNTIME", "llamacpp")
    import app.runtime.factory as factory

    importlib.reload(factory)
    rt = factory.runtime()

    assert rt.name == "llamacpp"
    with pytest.raises(NotImplementedError):
        rt.list_models()


def test_runtime_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv("AIHUB_RUNTIME", "unknown")
    import app.runtime.factory as factory

    importlib.reload(factory)

    with pytest.raises(ValueError, match="Unsupported AIHUB_RUNTIME"):
        factory.runtime()
