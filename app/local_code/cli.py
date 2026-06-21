"""Local Claude Code-style CLI powered by Local AI Hub runtimes."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path

from app.local_code.editing import apply_edit, list_edits, propose_file, reject_edit, show_edit
from app.local_code.indexer import build_project_index, format_index_context, search_project_index
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
    index_text = format_index_context(search_project_index(project, prompt))
    system_parts = [LOCAL_CODE_SYSTEM]
    if instruction_text:
        system_parts.append(instruction_text)
    if index_text:
        system_parts.append(index_text)
    system = "\n\n".join(system_parts)
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
        print("Usage: local-ai code ask <prompt>", file=sys.stderr)
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


def cmd_index(args: argparse.Namespace) -> int:
    data = build_project_index(Path(args.project))
    print(f"Indexed {len(data['files'])} files from {data['project']}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    query = " ".join(args.query).strip()
    if not query:
        print("Usage: local-ai code search <query>", file=sys.stderr)
        return 2
    matches = search_project_index(Path(args.project), query, limit=args.limit)
    if not matches:
        print("No indexed matches. Run: local-ai code index")
        return 0
    for item in matches:
        print(f"{item.path}\t{item.size} bytes")
    return 0


def cmd_propose(args: argparse.Namespace) -> int:
    content = Path(args.content_file).read_text(encoding="utf-8")
    edit = propose_file(Path(args.project), args.file, content, reason=args.reason or "")
    print(f"Queued edit {edit.id}: {edit.path}")
    print("Review with: local-ai code diff", edit.id)
    print("Apply with:  local-ai code apply", edit.id)
    return 0


def cmd_edits(_args: argparse.Namespace) -> int:
    edits = list_edits()
    if not edits:
        print("No pending Local Code edits.")
        return 0
    for edit in edits:
        print(f"{edit.id}\t{edit.path}\t{edit.reason}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    print(show_edit(args.edit_id))
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    print(apply_edit(args.edit_id))
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    print(reject_edit(args.edit_id))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-ai code",
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

    index = sub.add_parser("index", help="index project files for local-code context")
    index.set_defaults(func=cmd_index)

    search = sub.add_parser("search", help="search the Local Code project index")
    search.add_argument("query", nargs=argparse.REMAINDER)
    search.add_argument("--limit", type=int, default=8)
    search.set_defaults(func=cmd_search)

    propose = sub.add_parser("propose", help="queue a complete-file replacement for approval")
    propose.add_argument("--file", required=True, help="project-relative file to change")
    propose.add_argument("--content-file", required=True, help="file containing proposed new content")
    propose.add_argument("--reason", default="", help="reason shown in the approval queue")
    propose.set_defaults(func=cmd_propose)

    edits = sub.add_parser("edits", help="list pending Local Code edits")
    edits.set_defaults(func=cmd_edits)

    diff = sub.add_parser("diff", help="show one pending edit diff")
    diff.add_argument("edit_id")
    diff.set_defaults(func=cmd_diff)

    apply_cmd = sub.add_parser("apply", help="apply one approved edit")
    apply_cmd.add_argument("edit_id")
    apply_cmd.set_defaults(func=cmd_apply)

    reject = sub.add_parser("reject", help="reject one pending edit")
    reject.add_argument("edit_id")
    reject.set_defaults(func=cmd_reject)

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
