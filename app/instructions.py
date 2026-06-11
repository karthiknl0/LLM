"""Standing instructions — the hub's CLAUDE.md: whatever you write in
data/instructions.md is injected into every Chat and Agent system
prompt. Edit the file to permanently shape your assistant; changes
apply on the next message, no restart needed.
"""

from app.config import ROOT

INSTRUCTIONS_PATH = ROOT / "data" / "instructions.md"

TEMPLATE = """# My standing instructions

These rules apply to every conversation. Edit freely.

- Reply concisely and practically.
"""


def standing_instructions() -> str:
    """The user's always-on rules, or '' if the file is empty."""
    if not INSTRUCTIONS_PATH.exists():
        INSTRUCTIONS_PATH.write_text(TEMPLATE, encoding="utf-8")
    try:
        return INSTRUCTIONS_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
