"""Health checks: confirms Ollama, models, GPU, and data are in place,
and tells you exactly what to do about anything that's missing."""

import shutil

import ollama

from app.core.config import (
    CHAT_MODEL,
    DOCUMENTS_DIR,
    EMBED_MODEL,
    ROOT,
    VISION_MODEL,
)

OK, WARN, FAIL = "✅", "⚠️", "❌"


def _check_ollama() -> list[str]:
    try:
        listed = ollama.list()["models"]
        installed = {m["model"] for m in listed}
    except Exception as exc:
        return [
            f"{FAIL} Ollama server not reachable ({exc}). "
            "Start it with `ollama serve`."
        ]
    lines = [f"{OK} Ollama server is running ({len(installed)} models installed)"]
    for label, name in (
        ("Chat model", CHAT_MODEL),
        ("Vision model", VISION_MODEL),
        ("Embedding model", EMBED_MODEL),
    ):
        present = any(
            m == name or m.split(":")[0] == name for m in installed
        )
        if present:
            lines.append(f"{OK} {label} `{name}` is pulled")
        else:
            lines.append(f"{FAIL} {label} `{name}` missing — run `ollama pull {name}`")
    return lines


def _check_gpu() -> list[str]:
    try:
        import torch
    except ImportError:
        return [f"{WARN} PyTorch not installed — image/video generation disabled"]
    if not torch.cuda.is_available():
        return [
            f"{WARN} No CUDA GPU visible to PyTorch — generation will be "
            "very slow. Check your NVIDIA driver and the CUDA build of torch."
        ]
    free, total = torch.cuda.mem_get_info()
    return [
        f"{OK} GPU: {torch.cuda.get_device_name(0)} — "
        f"{free / 1e9:.1f} GB free of {total / 1e9:.1f} GB VRAM"
    ]


def _check_data() -> list[str]:
    lines = []
    documents = [p for p in DOCUMENTS_DIR.rglob("*") if p.is_file()]
    if documents:
        lines.append(f"{OK} {len(documents)} file(s) in data/documents/")
    else:
        lines.append(
            f"{WARN} No documents yet — drop PDFs/Excel/code into "
            "data/documents/ and index them in the Documents tab"
        )
    try:
        from app.memory import list_memories

        count = len(list_memories())
        lines.append(f"{OK} {count} memories/lessons stored")
    except Exception as exc:
        lines.append(f"{WARN} Memory store not readable: {exc}")

    usage = shutil.disk_usage(ROOT)
    free_gb = usage.free / 1e9
    icon = OK if free_gb > 30 else WARN
    lines.append(
        f"{icon} {free_gb:.0f} GB disk free "
        f"(models and outputs need room — keep 30+ GB free)"
    )
    return lines


def _check_email() -> list[str]:
    from app.services.mail import is_configured

    if is_configured():
        return [f"{OK} Email configured (read-only IMAP)"]
    return [
        f"{OK} Email not configured (optional — set AIHUB_IMAP_USER and "
        "AIHUB_IMAP_PASSWORD; see README)"
    ]


def _check_mcp() -> list[str]:
    from app.services import mcp

    servers = mcp.configured_servers()
    if not servers:
        return [
            f"{OK} No MCP servers configured (optional — add them in "
            "data/mcp.json)"
        ]
    tools = mcp.mcp_tools()
    return [
        f"{OK if tools else WARN} {len(servers)} MCP server(s) configured, "
        f"{len(tools)} tool(s) available"
        + ("" if tools else " — check the terminal for connection errors")
    ]


def run_checks() -> str:
    sections = (
        ("Ollama & models", _check_ollama),
        ("GPU", _check_gpu),
        ("Data", _check_data),
        ("Email", _check_email),
        ("MCP servers", _check_mcp),
    )
    report = ["## System status\n"]
    for title, check in sections:
        report.append(f"**{title}**")
        try:
            report += check()
        except Exception as exc:
            report.append(f"{FAIL} Check failed: {exc}")
        report.append("")
    return "\n\n".join(report)
