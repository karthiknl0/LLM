"""MCP client: connect the agent to Model Context Protocol servers.

Configure servers in data/mcp.json using the same shape as Claude
Desktop's config:

    {
      "mcpServers": {
        "filesystem": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/you/stuff"]
        }
      }
    }

Each connected server's tools appear to the agent as mcp_<server>_<tool>.
Servers run locally as subprocesses over stdio; connections are made
lazily on first use and kept open. Everything degrades gracefully: a
missing package, bad config, or dead server prints a warning and the
agent simply has fewer tools.
"""

import asyncio
import json
import threading
from contextlib import AsyncExitStack

from app.core.config import ROOT

CONFIG_PATH = ROOT / "data" / "mcp.json"
CONNECT_TIMEOUT = 120
CALL_TIMEOUT = 120


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text('{\n  "mcpServers": {}\n}\n', encoding="utf-8")
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get(
            "mcpServers", {}
        )
    except Exception as exc:
        print(f"[mcp] could not read {CONFIG_PATH.name}: {exc}")
        return {}


class _Manager:
    """Owns a background asyncio loop and persistent server sessions."""

    def __init__(self):
        self._lock = threading.Lock()
        self._started = False
        self._loop = None
        self._stack = None
        self._tools = []      # Ollama tool schemas
        self._functions = {}  # tool name -> callable(**kwargs) -> str

    def _run(self, coro, timeout):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout)

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
            servers = _load_config()
            if not servers:
                return
            try:
                import mcp  # noqa: F401  (the SDK package)
            except ImportError:
                print("[mcp] servers configured but the 'mcp' package is "
                      "not installed — pip install mcp")
                return

            self._loop = asyncio.new_event_loop()
            threading.Thread(
                target=self._loop.run_forever, daemon=True
            ).start()
            self._run(self._make_stack(), timeout=10)
            for name, spec in servers.items():
                try:
                    count = self._run(
                        self._connect(name, spec), timeout=CONNECT_TIMEOUT
                    )
                    print(f"[mcp] connected '{name}' ({count} tools)")
                except Exception as exc:
                    print(f"[mcp] could not connect '{name}': {exc}")

    async def _make_stack(self):
        self._stack = AsyncExitStack()

    async def _connect(self, name: str, spec: dict) -> int:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=spec["command"],
            args=spec.get("args", []),
            env=spec.get("env"),
        )
        read, write = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        listed = await session.list_tools()
        for tool in listed.tools:
            full_name = f"mcp_{name}_{tool.name}"
            self._tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": full_name,
                        "description": (tool.description or tool.name)[:1000],
                        "parameters": tool.inputSchema
                        or {"type": "object", "properties": {}},
                    },
                }
            )
            self._functions[full_name] = self._make_caller(session, tool.name)
        return len(listed.tools)

    def _make_caller(self, session, tool_name: str):
        async def _call_async(arguments: dict) -> str:
            result = await session.call_tool(tool_name, arguments)
            parts = [
                item.text
                for item in result.content
                if getattr(item, "text", None)
            ]
            return "\n".join(parts) or "(no text result)"

        def call(**kwargs) -> str:
            return self._run(_call_async(kwargs), timeout=CALL_TIMEOUT)

        return call


_manager = _Manager()


def mcp_tools() -> list[dict]:
    """Ollama tool schemas for every connected MCP server tool."""
    _manager.start()
    return list(_manager._tools)


def mcp_functions() -> dict:
    """Callables for every connected MCP server tool."""
    _manager.start()
    return dict(_manager._functions)


def configured_servers() -> list[str]:
    return list(_load_config())
