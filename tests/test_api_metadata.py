from app.api import server


class FakeRuntime:
    name = "fake"

    def list_models(self):
        return []


def test_health_includes_packages(monkeypatch):
    monkeypatch.setattr(server, "runtime", lambda: FakeRuntime())
    monkeypatch.setattr(server, "installed_models", lambda: ["qwen3.5:4b"])
    monkeypatch.setattr(server, "current_model", lambda: "writer")

    class Package:
        name = "writer"

    monkeypatch.setattr(server, "list_packages", lambda: [Package()])

    result = server.health()

    assert result["status"] == "ok"
    assert result["runtime"] == "fake"
    assert result["active_model"] == "writer"
    assert result["packages"] == ["writer"]


def test_v1_models_includes_runtime_models_and_packages(monkeypatch):
    monkeypatch.setattr(server, "runtime", lambda: FakeRuntime())

    class Model:
        name = "qwen3.5:4b"
        runtime = "fake"
        capabilities = ["chat"]
        size = 123
        family = "qwen"
        modified_at = "now"

    class Package:
        name = "writer"
        base = "qwen3.5:4b"
        capabilities = ["chat"]
        path = "data/models/writer/LocalModel.yaml"
        description = "Writing helper"

    monkeypatch.setattr(server, "list_models", lambda include_embeddings=False: [Model()])
    monkeypatch.setattr(server, "list_packages", lambda: [Package()])

    result = server.v1_models()
    ids = [item["id"] for item in result["data"]]

    assert "qwen3.5:4b" in ids
    assert "writer" in ids
    assert result["object"] == "list"
