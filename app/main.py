"""Local AI Hub — single Gradio app for all capabilities.

Run with:  python -m app.main
Then open: http://localhost:7860
"""

import gradio as gr

from app.chat import stream_chat
from app.config import CHAT_MODEL, DOCUMENTS_DIR, VISION_MODEL
from app.imagegen import generate_image
from app.rag import ask_documents, index_documents
from app.videogen import generate_video
from app.vision import analyze_media


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Local AI Hub") as demo:
        gr.Markdown("# Local AI Hub\nEverything runs on your own machine.")

        with gr.Tab("Chat"):
            gr.Markdown(f"Model: `{CHAT_MODEL}` (local via Ollama)")
            gr.ChatInterface(fn=stream_chat, type="messages")

        with gr.Tab("Documents"):
            gr.Markdown(
                f"Put PDFs, Excel/CSV files, and code into `{DOCUMENTS_DIR}`, "
                "then index them and ask questions."
            )
            index_btn = gr.Button("Index documents", variant="primary")
            index_status = gr.Markdown()
            index_btn.click(index_documents, outputs=index_status)

            doc_question = gr.Textbox(
                label="Question about your documents",
                placeholder="e.g. What does the Q3 sheet say about revenue?",
            )
            doc_answer = gr.Markdown()
            doc_question.submit(ask_documents, inputs=doc_question, outputs=doc_answer)

        with gr.Tab("Vision"):
            gr.Markdown(f"Model: `{VISION_MODEL}` — upload an image or a video.")
            media_file = gr.File(
                label="Image or video",
                file_types=["image", "video"],
                type="filepath",
            )
            vision_question = gr.Textbox(
                label="Question",
                placeholder="Describe this / What's the error in this screenshot? ...",
            )
            vision_btn = gr.Button("Analyze", variant="primary")
            vision_answer = gr.Markdown()
            vision_btn.click(
                analyze_media,
                inputs=[media_file, vision_question],
                outputs=vision_answer,
            )

        with gr.Tab("Generate Image"):
            gr.Markdown("SDXL Turbo — a few seconds per image. Saved to `outputs/`.")
            image_prompt = gr.Textbox(
                label="Prompt",
                placeholder="a cozy cabin in a snowy forest at dusk, photorealistic",
            )
            image_steps = gr.Slider(1, 8, value=4, step=1, label="Steps")
            image_btn = gr.Button("Generate", variant="primary")
            image_out = gr.Image(label="Result")
            image_status = gr.Markdown()
            image_btn.click(
                generate_image,
                inputs=[image_prompt, image_steps],
                outputs=[image_out, image_status],
            )

        with gr.Tab("Generate Video"):
            gr.Markdown(
                "LTX-Video — **experimental on 16 GB**. First use downloads "
                "~10 GB; each clip takes several minutes."
            )
            video_prompt = gr.Textbox(
                label="Prompt",
                placeholder="a paper boat drifting down a rainy street, cinematic",
            )
            video_seconds = gr.Slider(2, 6, value=3, step=1, label="Seconds")
            video_btn = gr.Button("Generate", variant="primary")
            video_out = gr.Video(label="Result")
            video_status = gr.Markdown()
            video_btn.click(
                generate_video,
                inputs=[video_prompt, video_seconds],
                outputs=[video_out, video_status],
            )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7860)
