"""Models and LocalModel packages Gradio tab."""

from __future__ import annotations

import gradio as gr

from app.session.model_catalog import catalog_summary, model_catalog_rows, set_active_from_catalog

CATALOG_HEADERS = ["Active", "Name", "Type", "Runtime/Base", "Capabilities"]


def refresh_catalog():
    """Return table rows and summary markdown for the catalog tab."""
    return model_catalog_rows(), catalog_summary()


def build_models_tab() -> None:
    """Build the Models / Packages tab inside an existing Blocks context."""
    gr.Markdown(
        "Manage installed runtime models and LocalModel package presets. "
        "Packages appear beside runtime models and can be selected as the active brain."
    )
    summary = gr.Markdown(catalog_summary())
    refresh_btn = gr.Button("Refresh catalog", variant="primary")
    table = gr.Dataframe(
        headers=CATALOG_HEADERS,
        value=model_catalog_rows(),
        interactive=False,
    )
    with gr.Row():
        active_name = gr.Textbox(
            label="Model or package name",
            placeholder="local-code, qwen3.5:4b, saree-assistant",
            scale=3,
        )
        set_btn = gr.Button("Set active", scale=1)
    status = gr.Markdown()

    refresh_btn.click(refresh_catalog, outputs=[table, summary])
    set_btn.click(set_active_from_catalog, inputs=active_name, outputs=status)
    set_btn.click(refresh_catalog, outputs=[table, summary])
