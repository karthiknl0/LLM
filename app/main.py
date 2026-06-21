"""Local AI Hub Gradio app.

Run with:  python -m app.main
Then open: http://localhost:7860
"""

from __future__ import annotations

import os

import gradio as gr

from app.agent import agent_chat
from app.chat.stream import stream_chat
from app.core.config import DOCUMENTS_DIR, VISION_MODEL, WORKSPACE_DIR
from app.media.imagegen import generate_image
from app.media.videogen import generate_video
from app.media.vision import analyze_media
from app.media.voice import transcribe_file, voice_chat
from app.memory import clear_memories, list_memories
from app.personas import DEFAULT_NAME, list_personas
from app.rag import ask_documents, index_documents
from app.repo import add_repo
from app.services.research import deep_research, research
from app.session.evals import list_sets, run_eval
from app.session.model_catalog import catalog_summary
from app.session.modelstate import current_model, installed_models, set_model
from app.session.promptlab import improve_prompt
from app.session.status import run_checks
from app.skills import list_skills
from app.subagents import team_run
from app.tools.screen import capture_and_analyze
from app.ui import work_queue
from app.ui.code_context import code_index_summary, index_project_for_code, instruction_summary, search_code_index
from app.ui.models_tab import build_models_tab

APP_CSS = """
.gradio-container { max-width: 1180px !important; margin: 0 auto !important; }
.app-title { display: flex; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.local-badge { border: 1px solid #36c48f66; border-radius: 999px; padding: 7px 11px; font-weight: 700; }
.model-row { align-items: flex-end; border: 1px solid #303741; border-radius: 8px; padding: 14px !important; margin-bottom: 16px; }
.model-status { align-self: stretch; display: flex; align-items: center; min-width: 220px; }
.aihub-chat { min-height: 440px !important; }
"""


def refresh_models():
    """Refresh runtime models and select a valid active chat model."""
    choices = installed_models()
    active = current_model()
    if choices and active not in choices:
        active = choices[0]
        set_model(active)
    return gr.Dropdown(choices=choices, value=active), f"Active model/package: `{active}`"


def agent_chat_ui(message, history, project_folder="", deep_answer=False, plan_mode=False):
    """Agent UI wrapper with a status output independent of chat painting."""
    last_reply = None
    for reply in agent_chat(message, history, project_folder, deep_answer, plan_mode):
        last_reply = reply
        yield reply, "AI is thinking…"
    if last_reply is not None:
        yield last_reply, "Ready"


def _run_research(question: str, deep: bool):
    return deep_research(question) if deep else research(question)


def local_code_status(project_folder: str) -> str:
    return "\n\n".join(
        [
            catalog_summary(),
            code_index_summary(project_folder),
            "Project instructions:\n" + instruction_summary(project_folder),
            f"Pending combined approvals: **{len(work_queue.rows())}**",
        ]
    )


def build_app() -> gr.Blocks:
    theme = gr.themes.Base(
        primary_hue="orange",
        neutral_hue="slate",
        radius_size="sm",
        spacing_size="sm",
        text_size="md",
    )
    with gr.Blocks(title="Local AI Hub", theme=theme, css=APP_CSS) as demo:
        gr.HTML(
            """
            <header class="app-title">
                <div>
                    <h1>Local AI Hub</h1>
                    <p>Private multimodal AI workstation running on this machine.</p>
                </div>
                <div class="local-badge">Local runtime</div>
            </header>
            """
        )

        with gr.Row(elem_classes=["model-row"]):
            model_dropdown = gr.Dropdown(
                choices=installed_models(),
                value=current_model(),
                label="Brain — runtime model or LocalModel package",
                scale=3,
            )
            model_refresh = gr.Button("Refresh models", scale=0, min_width=120)
            model_status = gr.Markdown(
                f"Active model/package: `{current_model()}`",
                elem_classes=["model-status"],
            )
        model_dropdown.change(set_model, inputs=model_dropdown, outputs=model_status)
        model_refresh.click(refresh_models, outputs=[model_dropdown, model_status])

        with gr.Tab("Models"):
            build_models_tab()

        with gr.Tab("Agent"):
            gr.Markdown(
                "The selected brain with tools. It now reads project instruction files and indexed code context for the selected project folder."
            )
            agent_project = gr.Textbox(label="Active project folder", value=str(WORKSPACE_DIR))
            with gr.Row():
                agent_index_btn = gr.Button("Index project for code context", variant="primary")
                agent_instructions_btn = gr.Button("Show project instructions")
                agent_index_status_btn = gr.Button("Show code index status")
            agent_context_out = gr.Markdown()
            agent_index_btn.click(index_project_for_code, inputs=agent_project, outputs=agent_context_out)
            agent_instructions_btn.click(instruction_summary, inputs=agent_project, outputs=agent_context_out)
            agent_index_status_btn.click(code_index_summary, inputs=agent_project, outputs=agent_context_out)
            agent_chatbot = gr.Chatbot(type="messages", elem_classes=["aihub-chat"])
            agent_status = gr.Markdown("Ready")
            gr.ChatInterface(
                fn=agent_chat_ui,
                type="messages",
                chatbot=agent_chatbot,
                multimodal=True,
                show_progress="minimal",
                additional_outputs=[agent_status],
                additional_inputs=[
                    agent_project,
                    gr.Checkbox(label="Deep answer", value=False),
                    gr.Checkbox(label="Plan mode", value=False),
                ],
            )

        with gr.Tab("Team"):
            gr.Markdown("Planner, workers, and reviewer for larger multi-part tasks.")
            team_task = gr.Textbox(label="Task", lines=3)
            team_btn = gr.Button("Run team", variant="primary")
            team_out = gr.Markdown()
            team_btn.click(team_run, inputs=team_task, outputs=team_out)

        with gr.Tab("Chat"):
            gr.Markdown("Plain chat with the selected brain and optional persona.")
            chat_catalog = gr.Markdown(catalog_summary())
            chat_catalog_refresh = gr.Button("Refresh active model/package")
            chat_catalog_refresh.click(catalog_summary, outputs=chat_catalog)
            plain_chatbot = gr.Chatbot(type="messages", elem_classes=["aihub-chat"])
            gr.ChatInterface(
                fn=stream_chat,
                type="messages",
                chatbot=plain_chatbot,
                additional_inputs=[
                    gr.Dropdown(choices=list_personas(), value=DEFAULT_NAME, label="Persona")
                ],
            )

        with gr.Tab("Documents"):
            gr.Markdown(f"Put PDFs, spreadsheets, and code into `{DOCUMENTS_DIR}`, then index and ask questions.")
            index_btn = gr.Button("Index documents", variant="primary")
            index_status = gr.Markdown()
            index_btn.click(index_documents, outputs=index_status)
            with gr.Row():
                code_project = gr.Textbox(label="Project folder for code index", value=str(WORKSPACE_DIR), scale=4)
                code_index_btn = gr.Button("Index project for Local Code", scale=1)
            code_search = gr.Textbox(label="Search code index", placeholder="runtime factory, model package, API endpoint")
            code_context_out = gr.Markdown()
            code_index_btn.click(index_project_for_code, inputs=code_project, outputs=code_context_out)
            code_search.submit(search_code_index, inputs=[code_project, code_search], outputs=code_context_out)
            doc_question = gr.Textbox(label="Question about your documents")
            doc_answer = gr.Markdown()
            doc_question.submit(ask_documents, inputs=doc_question, outputs=doc_answer)
            with gr.Row():
                repo_url = gr.Textbox(label="Repository URL", placeholder="https://github.com/owner/repo", scale=4)
                repo_btn = gr.Button("Clone & index", scale=1)
            repo_status = gr.Markdown()
            repo_btn.click(add_repo, inputs=repo_url, outputs=repo_status)

        with gr.Tab("Research"):
            gr.Markdown("Web research with citations. This tab uses internet search.")
            research_question = gr.Textbox(label="Research question")
            research_deep = gr.Checkbox(label="Deep research", value=False)
            research_btn = gr.Button("Research", variant="primary")
            research_answer = gr.Markdown()
            research_question.submit(_run_research, inputs=[research_question, research_deep], outputs=research_answer)
            research_btn.click(_run_research, inputs=[research_question, research_deep], outputs=research_answer)

        with gr.Tab("Vision"):
            gr.Markdown(f"Model: `{VISION_MODEL}` — upload an image or video.")
            media_file = gr.File(label="Image or video", file_types=["image", "video"], type="filepath")
            vision_question = gr.Textbox(label="Question")
            vision_btn = gr.Button("Analyze", variant="primary")
            vision_answer = gr.Markdown()
            vision_btn.click(analyze_media, inputs=[media_file, vision_question], outputs=vision_answer)

        with gr.Tab("Screen"):
            screen_question = gr.Textbox(label="Question", placeholder="What does this error mean?")
            screen_btn = gr.Button("Capture & analyze", variant="primary")
            screen_image = gr.Image(label="Screenshot")
            screen_answer = gr.Markdown()
            screen_btn.click(capture_and_analyze, inputs=screen_question, outputs=[screen_image, screen_answer])

        with gr.Tab("Voice"):
            mic = gr.Audio(sources=["microphone"], type="filepath", label="Your question")
            voice_btn = gr.Button("Ask", variant="primary")
            heard = gr.Textbox(label="You said", interactive=False)
            voice_reply = gr.Markdown(label="Reply")
            voice_audio = gr.Audio(label="Spoken reply", autoplay=True)
            voice_btn.click(voice_chat, inputs=mic, outputs=[heard, voice_reply, voice_audio])

        with gr.Tab("Transcribe"):
            transcribe_input = gr.File(label="Audio or video file", file_types=["audio", "video"], type="filepath")
            transcribe_btn = gr.Button("Transcribe", variant="primary")
            transcript_out = gr.Textbox(label="Transcript", lines=18, show_copy_button=True)
            transcribe_btn.click(transcribe_file, inputs=transcribe_input, outputs=transcript_out)

        with gr.Tab("Generate Image"):
            image_prompt = gr.Textbox(label="Prompt")
            image_steps = gr.Slider(1, 8, value=4, step=1, label="Steps")
            image_btn = gr.Button("Generate", variant="primary")
            image_out = gr.Image(label="Result")
            image_status = gr.Markdown()
            image_btn.click(generate_image, inputs=[image_prompt, image_steps], outputs=[image_out, image_status])

        with gr.Tab("Generate Video"):
            video_prompt = gr.Textbox(label="Prompt")
            video_seconds = gr.Slider(2, 6, value=3, step=1, label="Seconds")
            video_btn = gr.Button("Generate", variant="primary")
            video_out = gr.Video(label="Result")
            video_status = gr.Markdown()
            video_btn.click(generate_video, inputs=[video_prompt, video_seconds], outputs=[video_out, video_status])

        with gr.Tab("Memory"):
            with gr.Row():
                memory_refresh = gr.Button("Show memories", variant="primary")
                memory_clear = gr.Button("Forget everything")
            memory_table = gr.Dataframe(headers=["Date", "Type", "Memory"], interactive=False)
            memory_status = gr.Markdown()
            memory_refresh.click(list_memories, outputs=memory_table)
            memory_clear.click(clear_memories, outputs=memory_status)

        with gr.Tab("Skills"):
            skills_refresh = gr.Button("Show skills", variant="primary")
            skills_table = gr.Dataframe(headers=["Skill", "Description"], interactive=False)
            skills_refresh.click(list_skills, outputs=skills_table)

        with gr.Tab("Approvals"):
            gr.Markdown("Agent and Local Code file changes are shown together. Use the full ID such as `agent:abc123` or `code:def456`.")
            approvals_refresh = gr.Button("Refresh", variant="primary")
            approvals_table = gr.Dataframe(headers=["Source", "ID", "File", "Reason"], interactive=False)
            approvals_refresh.click(work_queue.rows, outputs=approvals_table)
            approval_id = gr.Textbox(label="Edit ID")
            with gr.Row():
                diff_btn = gr.Button("Show diff")
                approve_btn = gr.Button("Approve & apply", variant="primary")
                reject_btn = gr.Button("Reject")
            approval_out = gr.Markdown()
            diff_btn.click(work_queue.show, inputs=approval_id, outputs=approval_out)
            approve_btn.click(work_queue.accept, inputs=approval_id, outputs=approval_out)
            reject_btn.click(work_queue.drop, inputs=approval_id, outputs=approval_out)

        with gr.Tab("Prompt Helper"):
            prompt_in = gr.Textbox(label="Your draft prompt", lines=5)
            prompt_btn = gr.Button("Improve", variant="primary")
            prompt_out = gr.Markdown()
            prompt_btn.click(improve_prompt, inputs=prompt_in, outputs=prompt_out)

        with gr.Tab("Evals"):
            with gr.Row():
                eval_set = gr.Dropdown(choices=list_sets(), value=(list_sets() or [None])[0], label="Eval set")
                eval_persona = gr.Dropdown(choices=list_personas(), value=DEFAULT_NAME, label="Persona to test")
            eval_btn = gr.Button("Run eval", variant="primary")
            eval_out = gr.Markdown()
            eval_btn.click(run_eval, inputs=[eval_set, eval_persona], outputs=eval_out)

        with gr.Tab("Status"):
            status_btn = gr.Button("Run checks", variant="primary")
            status_out = gr.Markdown()
            status_btn.click(run_checks, outputs=status_out)
            status_project = gr.Textbox(label="Project folder for Local Code checks", value=str(WORKSPACE_DIR))
            local_status_btn = gr.Button("Run Local Code checks")
            local_status_out = gr.Markdown()
            local_status_btn.click(local_code_status, inputs=status_project, outputs=local_status_out)

    return demo


if __name__ == "__main__":
    from app.services.hooks import session_start

    session_start()
    host = os.environ.get("AIHUB_HOST", "127.0.0.1")
    port = int(os.environ.get("AIHUB_PORT", "7860"))
    password = os.environ.get("AIHUB_PASSWORD")
    auth = ("me", password) if password else None
    build_app().launch(server_name=host, server_port=port, auth=auth, inbrowser=True)
