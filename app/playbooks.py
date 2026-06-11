"""Playbook library: authored, reusable workflows the agent discovers
cheaply and loads on demand — progressive disclosure.

Each .md file in data/playbooks/ has YAML-ish frontmatter and a body:

    ---
    name: debug-a-failing-test
    description: Reproduce, isolate, and fix a failing test, then verify.
    tags: [debugging, testing]
    ---
    ## When to use
    ...
    ## Workflow
    1. ...

The agent always sees the cheap one-line descriptions (so it knows what
exists) and calls load_playbook(name) to pull the full workflow only
when relevant. This is the format from agentskills.io / the Anthropic
skills libraries — domain-neutral, so write playbooks for your own
recurring work (or drop in a published library, e.g. authorized
defensive-security playbooks).
"""

import re

from app.config import ROOT

PLAYBOOKS_DIR = ROOT / "data" / "playbooks"

SEED = {
    "debug-a-failing-test": {
        "description": "Reproduce, isolate, and fix a failing test, then verify the fix.",
        "tags": "debugging, testing",
        "body": (
            "## When to use\nA test is failing and you need to fix the "
            "cause, not the symptom.\n\n"
            "## Prerequisites\nThe repo is cloned in the workspace and the "
            "test command is known.\n\n"
            "## Workflow\n"
            "1. Run the failing test alone with run_command (e.g. "
            "'pytest path::test -q', cwd repos/<name>); capture the error.\n"
            "2. Read the code under test and the test itself; state your "
            "hypothesis for the cause.\n"
            "3. Make the smallest change that addresses the hypothesis.\n"
            "4. Re-run the test with run_command; if still failing, revise "
            "the hypothesis (don't pile on changes).\n"
            "5. Run the full test suite with run_command to check for "
            "regressions.\n\n"
            "## Verification\nThe target test passes and no previously "
            "passing test now fails."
        ),
    },
    "review-code-changes": {
        "description": "Review a repo's pending changes for bugs, ordered by severity.",
        "tags": "review, code-quality",
        "body": (
            "## When to use\nThe user asks to review changes in a cloned "
            "repo before committing or merging.\n\n"
            "## Workflow\n"
            "1. Get the diff: git_status, then run_command 'git diff' (and "
            "'git diff main...HEAD' for branch changes) in repos/<name>.\n"
            "2. For each changed file, read enough surrounding code to "
            "judge the change in context — never review a diff blind.\n"
            "3. Look for: logic errors, unhandled edge cases, broken "
            "callers of changed signatures, resource leaks, race "
            "conditions.\n"
            "4. Report findings ordered by severity with file:line, why it "
            "matters, and a concrete fix. If the change is good, say so — "
            "do not invent problems.\n\n"
            "## Verification\nEvery finding cites a real line from the "
            "diff; run the tests (run_command) if a finding claims "
            "breakage."
        ),
    },
    "simplify-code": {
        "description": "Find simplification and reuse opportunities in changed code.",
        "tags": "review, simplicity",
        "body": (
            "## When to use\nThe user wants changed code made simpler, "
            "not bug-hunted.\n\n"
            "## Workflow\n"
            "1. Get the diff (run_command 'git diff' in repos/<name>).\n"
            "2. For each hunk ask: could fewer lines do this? Is there an "
            "existing helper in the repo that already does it (search the "
            "indexed code)? Is any abstraction used only once?\n"
            "3. Propose the minimal rewrites — show before/after for each, "
            "keeping behavior identical.\n"
            "4. Apply only the ones the user approves; re-run tests after.\n\n"
            "## Verification\nTests pass before and after; line count went "
            "down or clarity demonstrably up."
        ),
    },
    "security-review": {
        "description": "Defensive security pass over a repo's pending changes.",
        "tags": "review, security",
        "body": (
            "## When to use\nThe user asks for a security review of "
            "changes in their own repo.\n\n"
            "## Workflow\n"
            "1. Get the diff and the touched files' full contents.\n"
            "2. Check for: unsanitized input reaching shell/SQL/eval/"
            "deserialization; path traversal on user-supplied paths; "
            "secrets or tokens committed in code or config; overly broad "
            "file/network permissions; missing auth checks on new "
            "endpoints; unsafe defaults.\n"
            "3. Check new dependencies: are they needed, maintained, and "
            "pinned?\n"
            "4. Report findings ordered by severity with file:line, the "
            "attack scenario in one sentence, and the fix. No findings is "
            "a valid result — say so plainly.\n\n"
            "## Verification\nEach finding points at real code in the "
            "diff, not a hypothetical."
        ),
    },
    "analyze-a-dataset": {
        "description": "Explore a CSV/Excel file and summarize findings with a chart.",
        "tags": "data, analysis",
        "body": (
            "## When to use\nThe user shares a data file and wants insight "
            "or a summary.\n\n"
            "## Prerequisites\nThe file is in data/workspace/.\n\n"
            "## Workflow\n"
            "1. With run_python, load the file with pandas and print "
            "shape, columns, dtypes, and .head().\n"
            "2. Report missing values and obvious data-quality issues.\n"
            "3. Compute the summary statistics that match the user's "
            "question.\n"
            "4. Save one clear matplotlib chart as a .png in the "
            "workspace.\n\n"
            "## Verification\nNumbers are computed by code (not guessed), "
            "and the chart file exists."
        ),
    },
}

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def _seed() -> None:
    if any(PLAYBOOKS_DIR.glob("*.md")):
        return
    for name, spec in SEED.items():
        (PLAYBOOKS_DIR / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: {spec['description']}\n"
            f"tags: [{spec['tags']}]\n---\n{spec['body']}\n",
            encoding="utf-8",
        )


def _parse(path):
    text = path.read_text(encoding="utf-8")
    match = _FRONT.match(text)
    if not match:
        return path.stem, "(no description)", text
    front, body = match.groups()
    desc = ""
    for line in front.splitlines():
        if line.strip().lower().startswith("description:"):
            desc = line.split(":", 1)[1].strip()
    return path.stem, desc or "(no description)", body.strip()


def catalog() -> list[tuple[str, str]]:
    """Cheap scan: (name, description) for every playbook."""
    _seed()
    return [(_parse(p)[0], _parse(p)[1]) for p in sorted(PLAYBOOKS_DIR.glob("*.md"))]


def catalog_hint() -> str:
    """One-line-per-playbook list for the agent's system prompt."""
    rows = catalog()
    if not rows:
        return ""
    listing = "\n".join(f"- {name}: {desc}" for name, desc in rows)
    return (
        "\n\nPlaybooks available — call load_playbook(name) to get the "
        "full workflow before doing one of these tasks:\n" + listing
    )


def load_playbook(name: str) -> str:
    """Full body of one playbook (the on-demand part of progressive disclosure)."""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", (name or "").strip())
    path = PLAYBOOKS_DIR / f"{safe}.md"
    if not path.exists():
        names = ", ".join(n for n, _ in catalog()) or "(none)"
        return f"No playbook '{name}'. Available: {names}"
    return _parse(path)[2]
