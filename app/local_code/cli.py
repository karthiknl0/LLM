"""Local Claude Code-style CLI powered by Local AI Hub runtimes."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path

from app.local_code.instructions import collect_project_instructions, format_instructions
from app.model_packages import package_messages, package_options, resolve_model_or_package
from app.runtime import runtime
from app.session.modelstate import current_model, set_model

LOCAL_CODE_SYSTEM = """You are Local Code, a local coding assistant.
You run through Local AI Hub's configured local model runtime.
You are not Claude and you do not call Anthropic APIs.
Be practical, concise, and careful with code.
Explain commands before suggesting them.
Do not claim files were changed unless the user or a tool actually changed them.
""".strip()


def _messages(prompt: str, project: Path) -> tuple[str, list[dict[str, str]], object | None]:
    requested = current_model()
    runtime_model, package = resolve_model_or_package(requested)
    runtime_model = runtime_model or requested
    instruction_text = format_instructions(collect_project_instructions(project))
    system = LOCAL_CODE_SYSTEM
    if instruction_text:
        system = f"{system}\n\n{instruction_text}"
    messages = package_messages(
        package,
        [{"role": "user", "content": prompt}],
        fallback_system=system,
    )
    return runtime_model, messages, package


def cmd_ask(args: argparse.Namespace) -> int:
    if args.model:
        set_model(args.model)
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        print("Usage: local-code ask <prompt>", file=sys.stderr)
        return 2
    runtime_model, messages, package = _messages(prompt, Path(args.project))
    options = package_options(package)
    for part in runtime().chat(
        model=runtime_model,
        messages=messages,
        stream=True,
        options=options,
    ):
        print(part["message"]["content"], end="", flush=True)
    print()
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    if args.model:
        set_model(args.model)
    project = Path(args.project)
    runtime_model, seed_messages, package = _messages(
        "Start a local coding session. Wait for my task.", project
    )
    history = seed_messages[:-1]
    options = package_options(package)
    print(f"Local Code — model: {current_model()} -> {runtime_model}")
    print("Type /exit or /quit to stop.\n")
    while True:
        try:
            user = input("code> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbye")
            return 0
        if not user:
            continue
        if user.lower() in {"/exit", "/quit", "exit", "quit"}:
            print("bye")
            return 0
        history.append({"role": "user", "content": user})
        print("ai> ", end="", flush=True)
        reply = ""
        for part in runtime().chat(
            model=runtime_model,
            messages=history,
            stream=True,
            options=options,
        ):
            chunk = part["message"]["content"]
            reply += chunk
            print(chunk, end="", flush=True)
        print("\n")
        history.append({"role": "assistant", "content": reply})


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.project) / "CLAUDE.md"
    if path.exists() and not args.force:
        print(f"{path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    path.write_text(
        "# Project Instructions\n\n"
        "Use local models only. Do not call paid cloud model APIs unless I explicitly ask.\n"
        "Explain code changes before suggesting them. Prefer small, testable steps.\n",
        encoding="utf-8",
    )
    print(f"Created {path}")
    return 0


def cmd_instructions(args: argparse.Namespace) -> int:
    files = collect_project_instructions(Path(args.project))
    if not files:
        print("No project instruction files found.")
        return 0
    for item in files:
        print(item.path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-code",
        description="Local Claude Code-style CLI powered by local models",
    )
    parser.add_argument("--project", default=".", help="project directory, default: current directory")
    parser.add_argument("--model", help="model or LocalModel package to use")
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="ask one coding question")
    ask.add_argument("prompt", nargs=argparse.REMAINDER)
    ask.set_defaults(func=cmd_ask)

    chat = sub.add_parser("chat", help="open an interactive local coding session")
    chat.set_defaults(func=cmd_chat)

    init = sub.add_parser("init", help="create a CLAUDE.md-style instruction file")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    instructions = sub.add_parser("instructions", help="list discovered project instruction files")
    instructions.set_defaults(func=cmd_instructions)

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
        print(f"local-code failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
