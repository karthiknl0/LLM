"""Local prompt evaluations: measure whether a prompt change helped,
instead of guessing. (The discipline from Anthropic's prompt-evaluations
course, run entirely against Ollama.)

Test cases live in data/evals/*.jsonl, one per line:
    {"input": "2+2 then *10", "criteria": "States the answer is 40."}

For each case the model answers (optionally under a chosen persona),
then the model grades its own answer against the criteria as a judge
(PASS/FAIL + reason). Output is a per-case table and a pass rate, so
you can compare two personas or prompt versions on the same set.
"""

import json
import re

import ollama

from app.core.config import ROOT
from app.session.modelstate import current_model
from app.personas.manager import DEFAULT_NAME, get_prompt

EVALS_DIR = ROOT / "data" / "evals"

ANSWER_SYSTEM = (
    "You are a helpful local AI assistant. Answer concisely."
)
JUDGE_PROMPT = (
    "You are a strict grader. Given a question, an answer, and the "
    "success criteria, decide if the answer meets the criteria. Reply "
    "on one line: PASS or FAIL, then a dash and a brief reason.\n\n"
    "Question: {input}\n\nAnswer: {answer}\n\nCriteria: {criteria}"
)

SEED = [
    {"input": "What is 17 * 23?", "criteria": "States the answer is 391."},
    {"input": "Name the capital of Japan.", "criteria": "Says Tokyo."},
    {
        "input": "Reverse the word 'python'.",
        "criteria": "Gives 'nohtyp'.",
    },
    {
        "input": "I feel stuck on a coding bug. One tip?",
        "criteria": "Gives a concrete debugging tip, not vague encouragement.",
    },
]


def _seed() -> None:
    EVALS_DIR.mkdir(parents=True, exist_ok=True)
    default = EVALS_DIR / "default.jsonl"
    if not any(EVALS_DIR.glob("*.jsonl")):
        default.write_text(
            "\n".join(json.dumps(c, ensure_ascii=False) for c in SEED) + "\n",
            encoding="utf-8",
        )


def list_sets() -> list[str]:
    _seed()
    return [p.stem for p in sorted(EVALS_DIR.glob("*.jsonl"))]


def _load(set_name: str) -> list[dict]:
    path = EVALS_DIR / f"{set_name}.jsonl"
    if not path.exists():
        return []
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return cases


def _judge(case_input: str, answer: str, criteria: str) -> tuple[bool, str]:
    response = ollama.chat(
        model=current_model(),
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    input=case_input, answer=answer, criteria=criteria
                ),
            }
        ],
    )
    verdict = re.sub(
        r"<think>.*?</think>", "", response["message"]["content"], flags=re.DOTALL
    ).strip()
    passed = verdict.upper().lstrip().startswith("PASS")
    return passed, verdict[:200]


def run_eval(set_name: str, persona: str = DEFAULT_NAME):
    """Generator yielding a live-updating markdown report."""
    cases = _load(set_name)
    if not cases:
        yield f"No cases in '{set_name}'. Add JSONL files to data/evals/."
        return

    system = get_prompt(persona) or ANSWER_SYSTEM
    rows, passed = [], 0
    for i, case in enumerate(cases):
        question = case.get("input", "")
        criteria = case.get("criteria", "")
        answer = ollama.chat(
            model=current_model(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
        )["message"]["content"]
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
        ok, reason = _judge(question, answer, criteria)
        passed += ok
        mark = "✅" if ok else "❌"
        rows.append(f"| {mark} | {question[:50]} | {reason[:80]} |")
        yield (
            f"### Eval: {set_name} · persona: {persona}\n"
            f"Running case {i + 1}/{len(cases)}…\n\n"
            "| | Input | Judge |\n|---|---|---|\n" + "\n".join(rows)
        )

    rate = 100 * passed / len(cases)
    yield (
        f"### Eval: {set_name} · persona: {persona}\n"
        f"**Score: {passed}/{len(cases)} ({rate:.0f}%)**\n\n"
        "| | Input | Judge |\n|---|---|---|\n" + "\n".join(rows)
    )
