from app.session import model_catalog


class FakeModel:
    def __init__(self, name):
        self.name = name
        self.runtime = "fake"
        self.capabilities = ["chat"]


class FakePackage:
    def __init__(self, name):
        self.name = name
        self.base = "base-model"
        self.capabilities = ["code"]


def test_model_catalog_rows_include_models_and_packages(monkeypatch):
    monkeypatch.setattr(model_catalog, "current_model", lambda: "pkg")
    monkeypatch.setattr(model_catalog, "list_models", lambda include_embeddings=True: [FakeModel("m1")])
    monkeypatch.setattr(model_catalog, "list_packages", lambda: [FakePackage("pkg")])

    rows = model_catalog.model_catalog_rows()

    assert rows[0][1] == "m1"
    assert rows[1][0] == "active"
    assert rows[1][2] == "LocalModel package"


def test_set_active_from_catalog_validates_name(monkeypatch):
    calls = []
    monkeypatch.setattr(model_catalog, "set_model", lambda name: calls.append(name) or f"set {name}")

    assert model_catalog.set_active_from_catalog("") == "Choose a model or package name."
    assert model_catalog.set_active_from_catalog(" local-code ") == "set local-code"
    assert calls == ["local-code"]
