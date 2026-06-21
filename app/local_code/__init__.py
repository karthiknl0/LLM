"""Local coding assistant CLI support.

This package provides a Claude Code-style local workflow powered by the
configured Local AI Hub runtime. It does not call Anthropic or any cloud model.
"""

from app.local_code.instructions import collect_project_instructions

__all__ = ["collect_project_instructions"]
