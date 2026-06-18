"""Local AI Hub.

On import we default Ollama's `chat` to `think=False`. The qwen3.5 brain is a
reasoning model: its hidden chain-of-thought added ~13x latency per call with
no quality gain for this app's uses, and a single Agent turn fans out to
several model calls (answer + memory + skill-learning + history compaction),
so leaving thinking on made even a "hi" take over a minute. Disabling it once
here covers every call site (chat, agent, team, research, evals, ...). Any
call that genuinely wants reasoning can still pass `think=True` explicitly.
"""

import ollama as _ollama

_real_chat = _ollama.chat


def _chat_no_think(*args, **kwargs):
    kwargs.setdefault("think", False)
    return _real_chat(*args, **kwargs)


_ollama.chat = _chat_no_think
