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


def test_llamacpp_chat_is_not_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(llamacpp_runtime, "GGUF_MODELS_DIR", tmp_path)
    rt = llamacpp_runtime.LlamaCppRuntime()

    try:
        rt.chat(model="demo", messages=[])
    except NotImplementedError as exc:
        assert "not implemented" in str(exc)
    else:
        raise AssertionError("expected error")
