"""Local AI Hub — single Gradio app for all capabilities.

Run with:  python -m app.main
Then open: http://localhost:7860
"""

import gradio as gr

from app.agent import agent_chat
from app.chat.stream import stream_chat
from app.core.config import CHAT_MODEL, DOCUMENTS_DIR, VISION_MODEL
from app.media.imagegen import generate_image
from app.memory import clear_memories, list_memories
from app.session.modelstate import current_model, installed_models, set_model
from app.personas import DEFAULT_NAME, list_personas
from app.rag import ask_documents, index_documents
from app.repo import add_repo
from app.services.research import deep_research, research
from app.tools.screen import capture_and_analyze
from app.skills import list_skills
from app.session.evals import list_sets, run_eval
from app.tools.file_ops import approve, list_pending, reject, show_diff
from app.session.promptlab import improve_prompt
from app.session.status import run_checks
from app.subagents import team_run
from app.media.videogen import generate_video
from app.media.vision import analyze_media
from app.media.voice import transcribe_file, voice_chat


APP_CSS = """
:root {
    --aihub-bg: #0d0f12;
    --aihub-panel: #171a1f;
    --aihub-panel-soft: #20242b;
    --aihub-border: #303741;
    --aihub-border-strong: #46515f;
    --aihub-text: #f4f6f8;
    --aihub-muted: #a6adb8;
    --aihub-accent: #f28c28;
    --aihub-accent-soft: rgba(242, 140, 40, 0.14);
    --aihub-green: #36c48f;
}

body,
.gradio-container {
    background:
        linear-gradient(180deg, rgba(242, 140, 40, 0.05), transparent 260px),
        var(--aihub-bg) !important;
    color: var(--aihub-text) !important;
    font-family:
        Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif !important;
}

.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
    padding: 24px 28px 18px !important;
}

.app-title {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 16px;
}

.brand-lockup h1 {
    margin: 0;
    font-size: 28px;
    line-height: 1.1;
    letter-spacing: 0;
    color: var(--aihub-text);
}

.brand-lockup p {
    margin: 9px 0 0;
    color: var(--aihub-muted);
    font-size: 14px;
}

.local-badge {
    border: 1px solid rgba(54, 196, 143, 0.42);
    background: rgba(54, 196, 143, 0.11);
    color: #a8f2d5;
    border-radius: 999px;
    padding: 7px 11px;
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
}

.model-row {
    align-items: flex-end;
    border: 1px solid var(--aihub-border);
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.035), transparent),
        var(--aihub-panel);
    border-radius: 8px;
    padding: 14px !important;
    margin-bottom: 16px;
}

.model-status {
    align-self: stretch;
    display: flex;
    align-items: center;
    color: var(--aihub-muted);
    min-width: 220px;
}

.model-status code {
    color: #ffd0a3;
    background: var(--aihub-accent-soft);
    border: 1px solid rgba(242, 140, 40, 0.28);
    border-radius: 6px;
    padding: 2px 6px;
}

.agent-status {
    border: 1px solid rgba(242, 140, 40, 0.35);
    background: var(--aihub-accent-soft);
    border-radius: 7px;
    color: #ffd0a3;
    font-weight: 700;
    margin: 0 0 10px;
    padding: 9px 12px;
}

.agent-status p {
    color: inherit !important;
    margin: 0 !important;
}

.tab-nav,
.tabs > .tab-nav {
    border-bottom: 1px solid var(--aihub-border) !important;
    gap: 4px;
    flex-wrap: wrap;
}

.tab-nav button {
    border: 0 !important;
    border-radius: 7px 7px 0 0 !important;
    color: #cbd3df !important;
    font-weight: 700 !important;
    opacity: 1 !important;
    padding: 11px 14px !important;
}

.tabs > .tab-wrapper button {
    color: #cbd3df !important;
    opacity: 1 !important;
}

.tabs > .tab-wrapper button.selected {
    color: #ff9d42 !important;
}

.tab-nav button:disabled {
    color: #808896 !important;
    opacity: 0.72 !important;
}

.tab-nav button.selected,
.tab-nav button[aria-selected="true"] {
    background: var(--aihub-accent-soft) !important;
    color: #ffb66e !important;
    box-shadow: inset 0 -2px 0 var(--aihub-accent) !important;
}

.tabitem {
    padding-top: 18px !important;
}

.prose,
.markdown,
.gradio-container p {
    color: var(--aihub-text);
}

.prose p,
.markdown p {
    color: var(--aihub-muted);
    line-height: 1.55;
}

.block,
.panel,
.form,
.input-container,
.output-class,
.aihub-chat,
.contain {
    border-color: var(--aihub-border) !important;
    border-radius: 8px !important;
}

.block,
.panel,
.form {
    background: var(--aihub-panel) !important;
}

label,
.wrap label,
.block-title,
.label-wrap,
.block-label {
    color: #dce2ea !important;
    font-weight: 700 !important;
}

label.float {
    background: #1a1f26 !important;
    border: 1px solid var(--aihub-border) !important;
    color: #dce2ea !important;
}

.label-wrap,
.block-label {
    background: #1a1f26 !important;
    border: 1px solid var(--aihub-border) !important;
    border-radius: 6px !important;
}

input,
textarea,
select,
.dropdown,
.wrap,
.wrap-inner {
    background: var(--aihub-panel-soft) !important;
    color: var(--aihub-text) !important;
    border-color: var(--aihub-border-strong) !important;
}

textarea:focus,
input:focus,
.wrap:focus-within {
    border-color: rgba(242, 140, 40, 0.72) !important;
    box-shadow: 0 0 0 3px rgba(242, 140, 40, 0.12) !important;
}

button.primary,
.primary {
    background: linear-gradient(180deg, #ff9c35, #de7415) !important;
    border-color: #f28c28 !important;
    color: #16100a !important;
    font-weight: 800 !important;
}

button.secondary,
button:not(.selected) {
    border-color: var(--aihub-border) !important;
}

.aihub-chat {
    min-height: 440px !important;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.025), transparent 180px),
        #111418 !important;
}

.message,
.message-wrap {
    border-radius: 8px !important;
}

.message.user {
    background: #303540 !important;
    border: 1px solid #47505d !important;
}

.message.bot {
    background: #171b21 !important;
    border: 1px solid var(--aihub-border) !important;
}

code {
    background: #252a32 !important;
    color: #f3d7b8 !important;
    border-radius: 5px;
    padding: 1px 5px;
}

table {
    border-color: var(--aihub-border) !important;
}

@media (max-width: 780px) {
    .gradio-container {
        padding: 16px !important;
    }

    .app-title {
        display: block;
    }

    .local-badge {
        display: inline-block;
        margin-top: 12px;
    }
}
"""


def refresh_models():
    """Refresh Ollama models and select a valid active chat model."""
    choices = installed_models()
    active = current_model()
    if choices and active not in choices:
        active = choices[0]
        set_model(active)
    return gr.Dropdown(choices=choices, value=active), f"Active model: `{active}`"


def agent_chat_ui(message, history, deep_answer=False, plan_mode=False):
    """Agent UI wrapper with a status output independent of chat painting."""
    last_reply = None
    for reply in agent_chat(message, history, deep_answer, plan_mode):
        last_reply = reply
        yield reply, "AI is thinking…"
    if last_reply is not None:
        yield last_reply, "Ready"


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
                <div class="brand-lockup">
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
                label="Brain — the Ollama model answering everywhere "
                "(chat, agent, team, research)",
                scale=3,
            )
            model_refresh = gr.Button("Refresh models", scale=0, min_width=120)
            model_status = gr.Markdown(
                f"Active model: `{current_model()}`",
                elem_classes=["model-status"],
            )
        model_dropdown.change(set_model, inputs=model_dropdown, outputs=model_status)
        model_refresh.click(
            refresh_models,
            outputs=[model_dropdown, model_status],
        )

        with gr.Tab("Agent"):
            gr.Markdown(
                "The selected brain, with tools — it decides by itself "
                "when to search your documents, research the web, run "
                "Python (workspace: `data/workspace/`), or generate an "
                "image. Attach images, videos, or data files with the 📎 "
                "button."
            )
            agent_chatbot = gr.Chatbot(
                type="messages",
                elem_classes=["aihub-chat"],
            )
            agent_status = gr.Markdown("Ready", elem_classes=["agent-status"])
            gr.ChatInterface(
                fn=agent_chat_ui,
                type="messages",
                chatbot=agent_chatbot,
                multimodal=True,
                show_progress="full",
                additional_outputs=[agent_status],
                additional_inputs=[
                    gr.Checkbox(
                        label="Deep answer — the model reviews its own draft "
                        "first (slower, more reliable)",
                        value=False,
                    ),
                    gr.Checkbox(
                        label="Plan mode — read-only: the agent explores and "
                        "proposes a plan; editing/execution tools are disabled "
                        "until you untick this",
                        value=False,
                    ),
                ],
            )

        with gr.Tab("Team"):
            gr.Markdown(
                "Multiple specialist agents on one big task: a planner "
                "splits it up, workers execute each part with the full "
                "toolset, and a reviewer combines everything. Slower than "
                "the Agent — use it for reports, comparisons, and "
                "multi-part jobs."
            )
            team_task = gr.Textbox(
                label="Task",
                lines=3,
                placeholder=(
                    "e.g. Compare the top 3 open-source TTS models, check "
                    "VRAM needs for each, and recommend one for a 16 GB GPU"
                ),
            )
            team_btn = gr.Button("Run team", variant="primary")
            team_out = gr.Markdown()
            team_btn.click(team_run, inputs=team_task, outputs=team_out)

        with gr.Tab("Chat"):
            gr.Markdown(
                "The selected brain, no tools. Pick "
                "a specialist persona below — or add your own as .md files "
                "in `data/personas/`."
            )
            plain_chatbot = gr.Chatbot(
                type="messages",
                elem_classes=["aihub-chat"],
            )
            gr.ChatInterface(
                fn=stream_chat,
                type="messages",
                chatbot=plain_chatbot,
                additional_inputs=[
                    gr.Dropdown(
                        choices=list_personas(),
                        value=DEFAULT_NAME,
                        label="Persona",
                    )
                ],
            )

        with gr.Tab("Voice"):
            gr.Markdown(
                "Talk to your assistant. Record a question, get a spoken "
                "answer. Replies use memory, just like the Chat tab."
            )
            mic = gr.Audio(sources=["microphone"], type="filepath", label="Your question")
            voice_btn = gr.Button("Ask", variant="primary")
            heard = gr.Textbox(label="You said", interactive=False)
            voice_reply = gr.Markdown(label="Reply")
            voice_audio = gr.Audio(label="Spoken reply", autoplay=True)
            voice_btn.click(
                voice_chat, inputs=mic, outputs=[heard, voice_reply, voice_audio]
            )

        with gr.Tab("Transcribe"):
            gr.Markdown(
                "Turn any audio or video file into a timestamped transcript "
                "(meetings, voice notes, lectures). Runs locally with Whisper."
            )
            transcribe_input = gr.File(
                label="Audio or video file",
                file_types=["audio", "video"],
                type="filepath",
            )
            transcribe_btn = gr.Button("Transcribe", variant="primary")
            transcript_out = gr.Textbox(
                label="Transcript", lines=18, show_copy_button=True
            )
            transcribe_btn.click(
                transcribe_file, inputs=transcribe_input, outputs=transcript_out
            )

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

            gr.Markdown(
                "**Chat with a codebase** — paste a GitHub URL: it is "
                "shallow-cloned into your documents and indexed, then ask "
                "about it above."
            )
            with gr.Row():
                repo_url = gr.Textbox(
                    label="Repository URL",
                    placeholder="https://github.com/owner/repo",
                    scale=4,
                )
                repo_btn = gr.Button("Clone & index", scale=1)
            repo_status = gr.Markdown()
            repo_btn.click(add_repo, inputs=repo_url, outputs=repo_status)

        with gr.Tab("Research"):
            gr.Markdown(
                "Ask about anything on the web — your local model searches, "
                "reads the top pages, and answers with citations. The only "
                "tab that uses the internet (free search, no API keys)."
            )
            research_question = gr.Textbox(
                label="Research question",
                placeholder="e.g. What are the best open-source TTS models in 2026?",
            )
            research_deep = gr.Checkbox(
                label="Deep research — multiple search angles + a "
                "verification pass (slower, better for complex questions)",
                value=False,
            )
            research_btn = gr.Button("Research", variant="primary")
            research_answer = gr.Markdown()

            def _run_research(question, deep):
                return deep_research(question) if deep else research(question)

            research_question.submit(
                _run_research,
                inputs=[research_question, research_deep],
                outputs=research_answer,
            )
            research_btn.click(
                _run_research,
                inputs=[research_question, research_deep],
                outputs=research_answer,
            )

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

        with gr.Tab("Screen"):
            gr.Markdown(
                "Capture this computer's screen and ask the vision model "
                "about it — errors, windows, anything you're looking at. "
                "The screenshot never leaves your machine. (Captures the "
                "desktop running the app, even when you browse from a phone.)"
            )
            screen_question = gr.Textbox(
                label="Question (optional)",
                placeholder="What does this error message mean?",
            )
            screen_btn = gr.Button("Capture & analyze", variant="primary")
            screen_image = gr.Image(label="Screenshot")
            screen_answer = gr.Markdown()
            screen_btn.click(
                capture_and_analyze,
                inputs=screen_question,
                outputs=[screen_image, screen_answer],
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

        with gr.Tab("Memory"):
            gr.Markdown(
                "The assistant remembers facts about you across sessions, "
                "and learns lessons when you correct it. Everything is "
                "stored locally — review or wipe it any time."
            )
            with gr.Row():
                memory_refresh = gr.Button("Show memories", variant="primary")
                memory_clear = gr.Button("Forget everything")
            memory_table = gr.Dataframe(
                headers=["Date", "Type", "Memory"], interactive=False
            )
            memory_status = gr.Markdown()
            memory_refresh.click(list_memories, outputs=memory_table)
            memory_clear.click(clear_memories, outputs=memory_status)

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

        with gr.Tab("Skills"):
            gr.Markdown(
                "Functions the agent taught itself by solving your tasks. "
                "Each is a plain Python file in `data/skills/` — edit or "
                "delete them freely. The agent imports relevant ones in "
                "future `run_python` calls instead of rewriting them."
            )
            skills_refresh = gr.Button("Show skills", variant="primary")
            skills_table = gr.Dataframe(
                headers=["Skill", "Description"], interactive=False
            )
            skills_refresh.click(list_skills, outputs=skills_table)

        with gr.Tab("Approvals"):
            gr.Markdown(
                "File edits the agent proposed. **Nothing is written until "
                "you approve it here.** Approved edits back up the original "
                "to `data/backups/` first."
            )
            approvals_refresh = gr.Button("Refresh", variant="primary")
            approvals_table = gr.Dataframe(
                headers=["ID", "File", "Reason"], interactive=False
            )
            approvals_refresh.click(list_pending, outputs=approvals_table)
            approval_id = gr.Textbox(label="Edit ID", placeholder="e.g. 3f9a1c2b")
            with gr.Row():
                diff_btn = gr.Button("Show diff")
                approve_btn = gr.Button("Approve & apply", variant="primary")
                reject_btn = gr.Button("Reject")
            approval_out = gr.Markdown()
            diff_btn.click(show_diff, inputs=approval_id, outputs=approval_out)
            approve_btn.click(approve, inputs=approval_id, outputs=approval_out)
            reject_btn.click(reject, inputs=approval_id, outputs=approval_out)

        with gr.Tab("Prompt Helper"):
            gr.Markdown(
                "Paste a rough prompt; get a stronger version that applies "
                "prompt-engineering techniques (clear instructions, role, "
                "data separation, output format, examples). Handy for "
                "writing personas, playbooks, and eval criteria."
            )
            prompt_in = gr.Textbox(
                label="Your draft prompt", lines=5,
                placeholder="e.g. summarize this article",
            )
            prompt_btn = gr.Button("Improve", variant="primary")
            prompt_out = gr.Markdown()
            prompt_btn.click(improve_prompt, inputs=prompt_in, outputs=prompt_out)

        with gr.Tab("Evals"):
            gr.Markdown(
                "Measure prompt quality instead of guessing. The model "
                "answers each test case, then grades itself against the "
                "criteria (LLM-as-judge). Run the same set under different "
                "personas to compare. Add your own sets as JSONL files in "
                "`data/evals/`."
            )
            with gr.Row():
                eval_set = gr.Dropdown(
                    choices=list_sets(),
                    value=(list_sets() or [None])[0],
                    label="Eval set",
                )
                eval_persona = gr.Dropdown(
                    choices=list_personas(),
                    value=DEFAULT_NAME,
                    label="Persona to test",
                )
            eval_btn = gr.Button("Run eval", variant="primary")
            eval_out = gr.Markdown()
            eval_btn.click(
                run_eval, inputs=[eval_set, eval_persona], outputs=eval_out
            )

        with gr.Tab("Status"):
            gr.Markdown(
                "Checks that Ollama, the models, your GPU, and your data "
                "are all in place — and what to do if not."
            )
            status_btn = gr.Button("Run checks", variant="primary")
            status_out = gr.Markdown()
            status_btn.click(run_checks, outputs=status_out)

    return demo


if __name__ == "__main__":
    import os

    from app.services.hooks import session_start

    session_start()

    # AIHUB_HOST=0.0.0.0 exposes the app on your LAN (e.g. for your
    # phone); set AIHUB_PASSWORD to require a login when you do.
    host = os.environ.get("AIHUB_HOST", "127.0.0.1")
    port = int(os.environ.get("AIHUB_PORT", "7860"))
    password = os.environ.get("AIHUB_PASSWORD")
    auth = ("me", password) if password else None
    build_app().launch(
        server_name=host, server_port=port, auth=auth, inbrowser=True
    )
