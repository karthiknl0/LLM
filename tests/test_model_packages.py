from pathlib import Path

import pytest

from app.model_packages import manager


def test_list_packages_loads_localmodel_yaml(tmp_path, monkeypatch):
    packages_dir = tmp_path / "data" / "models"
    package_dir = packages_dir / "saree-assistant"
    package_dir.mkdir(parents=True)
    (package_dir / "LocalModel.yaml").write_text(
        """
name: saree-assistant
description: Sales and inventory helper
base: qwen3.5:4b
system: |
  You help with saree sales and stock planning.
parameters:
  temperature: 0.4
capabilities:
  - chat
  - code
rag:
  collections:
    - documents
tools:
  - documents
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(manager, "ROOT", tmp_path)
    monkeypatch.setattr(manager, "PACKAGES_DIR", packages_dir)

    packages = manager.list_packages()

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "saree-assistant"
    assert package.base == "qwen3.5:4b"
    assert package.parameters == {"temperature": 0.4}
    assert package.capabilities == ["chat", "code"]
    assert package.rag == {"collections": ["documents"]}
    assert package.tools == ["documents"]


def test_resolve_model_or_package_returns_base_for_package(tmp_path, monkeypatch):
    packages_dir = tmp_path / "data" / "models" / "writer"
    packages_dir.mkdir(parents=True)
    (packages_dir / "LocalModel.yaml").write_text(
        "name: writer\nbase: qwen3.5:4b\nsystem: Write clearly.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(manager, "ROOT", tmp_path)
    monkeypatch.setattr(manager, "PACKAGES_DIR", tmp_path / "data" / "models")

    runtime_model, package = manager.resolve_model_or_package("writer")

    assert runtime_model == "qwen3.5:4b"
    assert package is not None
    assert package.name == "writer"


def test_package_messages_prepends_system_prompt():
    package = manager.LocalModelPackage(
        name="writer",
        base="qwen3.5:4b",
        path="data/models/writer/LocalModel.yaml",
        system="Write clearly.",
    )

    messages = manager.package_messages(
        package,
        [{"role": "user", "content": "Hello"}],
        fallback_system="Be concise.",
    )

    assert messages[0]["role"] == "system"
    assert "Write clearly." in messages[0]["content"]
    assert "Be concise." in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Hello"}


def test_invalid_package_requires_base(tmp_path, monkeypatch):
    packages_dir = tmp_path / "data" / "models" / "broken"
    packages_dir.mkdir(parents=True)
    (packages_dir / "LocalModel.yaml").write_text("name: broken\n", encoding="utf-8")

    monkeypatch.setattr(manager, "ROOT", tmp_path)
    monkeypatch.setattr(manager, "PACKAGES_DIR", tmp_path / "data" / "models")

    with pytest.raises(ValueError, match="base"):
        manager.list_packages()
