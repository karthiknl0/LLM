import sys
import types

import pytest

from app.runtime import llamacpp_runtime


def test_llamacpp_lists_model_files(tmp_path, monkeypatch):
    models_dir = tmp_path / "gguf"
    models_dir.mkdir()
    model_path = models_dir / "demo.gguf"
    model_path.write_text("demo", encoding="utf-8")

    monkeypatch.setattr(llamacpp_runtime, "GGUF_MODELS_DIR", models_dir)

    rt = llamacpp_runtime.LlamaCppRuntime()
    models = rt.list_models()

    assert len(models) == 1
    assert models[0]["model"] == "demo"
    assert models[0]["path"] == "demo.gguf"
    assert rt.list_model_names() == ["demo"]


def test_llamacpp_missing_package_message(tmp_path, monkeypatch):
    models_dir = tmp_path / "gguf"
    models_dir.mkdir()
    (models_dir / "demo.gguf").write_text("demo", encoding="utf-8")
    monkeypatch.setattr(llamacpp_runtime, "GGUF_MODELS_DIR", models_dir)
    monkeypatch.setitem(sys.modules, "llama_cpp", None)

    rt = llamacpp_runtime.LlamaCppRuntime()

    with pytest.raises(RuntimeError, match="llama-cpp-python"):
        rt.generate(model="demo", prompt="hello")


def test_llamacpp_generate_with_fake_backend(tmp_path, monkeypatch):
    models_dir = tmp_path / "gguf"
    models_dir.mkdir()
    (models_dir / "demo.gguf").write_text("demo", encoding="utf-8")
    monkeypatch.setattr(llamacpp_runtime, "GGUF_MODELS_DIR", models_dir)

    class FakeLlama:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def create_completion(self, **kwargs):
            return {"choices": [{"text": "hi"}], "kwargs": kwargs}

    fake_module = types.SimpleNamespace(Llama=FakeLlama)
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    rt = llamacpp_runtime.LlamaCppRuntime()
    result = rt.generate(model="demo", prompt="hello")

    assert result["response"] == "hi"
    assert result["done"] is True


def test_llamacpp_chat_with_fake_backend(tmp_path, monkeypatch):
    models_dir = tmp_path / "gguf"
    models_dir.mkdir()
    (models_dir / "demo.gguf").write_text("demo", encoding="utf-8")
    monkeypatch.setattr(llamacpp_runtime, "GGUF_MODELS_DIR", models_dir)

    class FakeLlama:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def create_chat_completion(self, **kwargs):
            return {"choices": [{"message": {"content": "hello"}}], "kwargs": kwargs}

    fake_module = types.SimpleNamespace(Llama=FakeLlama)
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    rt = llamacpp_runtime.LlamaCppRuntime()
    result = rt.chat(model="demo", messages=[{"role": "user", "content": "hi"}])

    assert result["message"]["content"] == "hello"
    assert result["done"] is True
