"""Model/package catalog helpers for UI and CLI surfaces."""

from __future__ import annotations

from app.model_packages import list_packages
from app.models import list_models
from app.runtime.factory import runtime
from app.session.modelstate import current_model, set_model


def model_catalog_rows() -> list[tuple[str, str, str, str, str]]:
    """Return rows for a models/packages table."""
    rows: list[tuple[str, str, str, str, str]] = []
    active = current_model()
    for model in list_models(include_embeddings=True):
        rows.append(
            (
                "active" if model.name == active else "",
                model.name,
                "runtime model",
                model.runtime,
                ",".join(model.capabilities),
            )
        )
    for package in list_packages():
        rows.append(
            (
                "active" if package.name == active else "",
                package.name,
                "LocalModel package",
                package.base,
                ",".join(package.capabilities),
            )
        )
    return rows


def catalog_summary() -> str:
    packages = list_packages()
    models = list_models(include_embeddings=True)
    return (
        f"Runtime: `{runtime().name}`  \n"
        f"Active model/package: `{current_model()}`  \n"
        f"Runtime models: **{len(models)}**  \n"
        f"LocalModel packages: **{len(packages)}**"
    )


def set_active_from_catalog(name: str) -> str:
    if not name.strip():
        return "Choose a model or package name."
    return set_model(name.strip())
