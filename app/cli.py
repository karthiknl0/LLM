"""Command-line interface for Local AI Hub.

This is the first roadmap step toward an Ollama-style local LLM platform.
It intentionally reuses the existing Ollama-backed model state, chat, and
status modules instead of introducing a second runtime path.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable

import ollama

from app.session.modelstate import current_model, installed_models, set_model


def _print_markdown(text: str) -> None:
    """Print markdown-ish app output in a terminal-friendly way."""
    print(text.strip())


def _chat_once(prompt: str, model: str | None = None, stream: bool = True) -> str:
    """Send one prompt to the active local model and optionally stream output."""
    selected_model = model or current_model()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful local AI assistant running entirely on the "
                "user's own computer. Be concise and practical."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    if not stream:
        response = ollama.chat(model=selected_model, messages=messages, stream=False)
        return response["message"]["content"]

    reply = ""
    for part in ollama.chat(model=selected_model, messages=messages, stream=True):
        chunk = part["message"]["content"]
        reply += chunk
        print(chunk, end="", flush=True)
    print()
    return reply


def cmd_list(_args: argparse.Namespace) -> int:
    """List installed chat-capable Ollama models."""
    active = current_model()
    models = installed_models()
    if not models:
        print("No chat-capable models found. Try: ollama pull qwen3.5:4b")
        return 1
    for name in models:
        marker = "*" if name == active else " "
        print(f"{marker} {name}")
    return 0


def cmd_model(args: argparse.Namespace) -> int:
    """Show or switch the active model."""
    if args.name:
        _print_markdown(set_model(args.name))
    else:
        print(f"Active model: {current_model()}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run one prompt against a local model."""
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        print("Usage: local-ai run [--model MODEL] <prompt>", file=sys.stderr)
        return 2
    if args.model:
        set_model(args.model)
    _chat_once(prompt, model=args.model, stream=not args.no_stream)
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    """Open an interactive terminal chat."""
    if args.model:
        set_model(args.model)
    model = current_model()
    print(f"Local AI Hub chat — model: {model}")
    print("Type /exit, /quit, or Ctrl-C to stop.\n")

    history: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful local AI assistant running entirely on the "
                "user's own computer. Be concise and practical."
            ),
        }
    ]

    while True:
        try:
            user_message = input("you> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbye")
            return 0

        if not user_message:
            continue
        if user_message.lower() in {"/exit", "/quit", "exit", "quit"}:
            print("bye")
            return 0

        history.append({"role": "user", "content": user_message})
        print("ai> ", end="", flush=True)
        reply = ""
        for part in ollama.chat(model=current_model(), messages=history, stream=True):
            chunk = part["message"]["content"]
            reply += chunk
            print(chunk, end="", flush=True)
        print("\n")
        history.append({"role": "assistant", "content": reply})


def cmd_status(_args: argparse.Namespace) -> int:
    """Run existing Local AI Hub health checks."""
    from app.session.status import run_checks

    _print_markdown(run_checks())
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    """Pull a model through Ollama."""
    print(f"Pulling {args.model}...")
    for event in ollama.pull(args.model, stream=True):
        status = event.get("status")
        digest = event.get("digest")
        completed = event.get("completed")
        total = event.get("total")
        suffix = ""
        if completed and total:
            suffix = f" ({completed}/{total})"
        elif digest:
            suffix = f" {digest[:12]}"
        if status:
            print(f"{status}{suffix}")
    return 0


def cmd_rm(args: argparse.Namespace) -> int:
    """Remove a model through Ollama."""
    ollama.delete(args.model)
    print(f"Removed {args.model}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the existing Gradio Local AI Hub server."""
    from app.main import build_app
    from app.services.hooks import session_start

    host = args.host or os.environ.get("AIHUB_HOST", "127.0.0.1")
    port = args.port or int(os.environ.get("AIHUB_PORT", "7860"))
    password = args.password or os.environ.get("AIHUB_PASSWORD")
    auth = ("me", password) if password else None

    session_start()
    print(f"Starting Local AI Hub UI at http://{host}:{port}")
    build_app().launch(server_name=host, server_port=port, auth=auth, inbrowser=args.browser)
    return 0


def cmd_api(args: argparse.Namespace) -> int:
    """Start the OpenAI/Ollama-compatible API server."""
    import uvicorn

    host = args.host or os.environ.get("AIHUB_API_HOST", "127.0.0.1")
    port = args.port or int(os.environ.get("AIHUB_API_PORT", "11435"))
    print(f"Starting Local AI Hub API at http://{host}:{port}")
    print(f"OpenAI-compatible base URL: http://{host}:{port}/v1")
    uvicorn.run("app.api.server:app", host=host, port=port, reload=args.reload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-ai",
        description="Local AI Hub command-line interface",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="list installed chat-capable models")
    list_parser.set_defaults(func=cmd_list)

    model_parser = sub.add_parser("model", help="show or switch the active model")
    model_parser.add_argument("name", nargs="?", help="model name to activate")
    model_parser.set_defaults(func=cmd_model)

    run_parser = sub.add_parser("run", help="run one prompt")
    run_parser.add_argument("prompt", nargs=argparse.REMAINDER, help="prompt text")
    run_parser.add_argument("--model", help="model to use for this prompt")
    run_parser.add_argument("--no-stream", action="store_true", help="print only the final reply")
    run_parser.set_defaults(func=cmd_run)

    chat_parser = sub.add_parser("chat", help="open an interactive terminal chat")
    chat_parser.add_argument("--model", help="model to use for the chat session")
    chat_parser.set_defaults(func=cmd_chat)

    status_parser = sub.add_parser("status", help="check Ollama, models, GPU, and data")
    status_parser.set_defaults(func=cmd_status)

    doctor_parser = sub.add_parser("doctor", help="alias for status")
    doctor_parser.set_defaults(func=cmd_status)

    pull_parser = sub.add_parser("pull", help="pull a model through Ollama")
    pull_parser.add_argument("model", help="model name, for example qwen3.5:4b")
    pull_parser.set_defaults(func=cmd_pull)

    rm_parser = sub.add_parser("rm", help="remove a model through Ollama")
    rm_parser.add_argument("model", help="model name to remove")
    rm_parser.set_defaults(func=cmd_rm)

    serve_parser = sub.add_parser("serve", help="start the Local AI Hub UI server")
    serve_parser.add_argument("--host", help="host to bind, default: AIHUB_HOST or 127.0.0.1")
    serve_parser.add_argument("--port", type=int, help="port to bind, default: AIHUB_PORT or 7860")
    serve_parser.add_argument("--password", help="optional UI password; username is 'me'")
    serve_parser.add_argument("--browser", action="store_true", help="open the browser automatically")
    serve_parser.set_defaults(func=cmd_serve)

    api_parser = sub.add_parser("api", help="start the OpenAI/Ollama-compatible API server")
    api_parser.add_argument("--host", help="host to bind, default: AIHUB_API_HOST or 127.0.0.1")
    api_parser.add_argument("--port", type=int, help="port to bind, default: AIHUB_API_PORT or 11435")
    api_parser.add_argument("--reload", action="store_true", help="reload API server on code changes")
    api_parser.set_defaults(func=cmd_api)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nCancelled")
        return 130
    except Exception as exc:
        print(f"local-ai failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
