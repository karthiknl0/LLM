from app.models import manager


class FakeRuntime:
    name = "fake"

    def list_models(self):
        return [
            {
                "model": "qwen3.5:4b",
                "size": 123,
                "modified_at": "2026-01-01T00:00:00Z",
                "details": {"family": "qwen"},
            },
            {
                "model": "nomic-embed-text",
                "size": 456,
                "details": {"family": "nomic"},
            },
            {
                "model": "qwen2.5-coder:14b",
                "size": 789,
                "details": {"family": "qwen"},
            },
        ]

    def pull_model(self, name, *, stream=True):
        return [{"status": "ok", "model": name, "stream": stream}]

    def delete_model(self, name):
        return {"deleted": name}


def test_list_models_normalizes_metadata(monkeypatch):
    monkeypatch.setattr(manager, "runtime", lambda: FakeRuntime())

    models = manager.list_models(include_embeddings=True)

    assert [m.name for m in models] == [
        "qwen3.5:4b",
        "nomic-embed-text",
        "qwen2.5-coder:14b",
    ]
    assert models[0].runtime == "fake"
    assert "chat" in models[0].capabilities
    assert "embedding" in models[1].capabilities
    assert "code" in models[2].capabilities


def test_chat_model_names_hide_embeddings(monkeypatch):
    monkeypatch.setattr(manager, "runtime", lambda: FakeRuntime())

    names = manager.chat_model_names()

    assert "qwen3.5:4b" in names
    assert "qwen2.5-coder:14b" in names
    assert "nomic-embed-text" not in names


def test_pull_and_remove_delegate_to_runtime(monkeypatch):
    fake = FakeRuntime()
    monkeypatch.setattr(manager, "runtime", lambda: fake)

    assert manager.pull_model("abc", stream=False) == [
        {"status": "ok", "model": "abc", "stream": False}
    ]
    assert manager.remove_model("abc") == {"deleted": "abc"}
