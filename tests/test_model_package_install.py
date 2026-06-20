from app.model_packages import manager


def test_install_package_file_copies_to_packages_dir(tmp_path, monkeypatch):
    source = tmp_path / "LocalModel.yaml"
    source.write_text("name: demo\nbase: qwen3.5:4b\n", encoding="utf-8")
    packages_dir = tmp_path / "data" / "models"

    monkeypatch.setattr(manager, "ROOT", tmp_path)
    monkeypatch.setattr(manager, "PACKAGES_DIR", packages_dir)

    package = manager.install_package_file(source)
    target = packages_dir / "demo" / "LocalModel.yaml"

    assert package.name == "demo"
    assert package.base == "qwen3.5:4b"
    assert package.path == "data/models/demo/LocalModel.yaml"
    assert target.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
