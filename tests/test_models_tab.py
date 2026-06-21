from app.ui import models_tab


def test_refresh_catalog_uses_catalog_helpers(monkeypatch):
    monkeypatch.setattr(models_tab, "model_catalog_rows", lambda: [("active", "local-code", "LocalModel package", "qwen3.5:4b", "code")])
    monkeypatch.setattr(models_tab, "catalog_summary", lambda: "summary")

    rows, summary = models_tab.refresh_catalog()

    assert rows[0][1] == "local-code"
    assert summary == "summary"


def test_catalog_headers_are_stable():
    assert models_tab.CATALOG_HEADERS == ["Active", "Name", "Type", "Runtime/Base", "Capabilities"]
