"""Team mode: multiple specialist agents tackle one big task —
a planner splits it into subtasks, workers execute each part with the
full toolset, and a reviewer combines everything into one answer.
"""

import re

import ollama

from app.agent.runner import run_with_tools
from app.session.modelstate import current_model

MAX_SUBTASKS = 4

PLANNER_SYSTEM = (
    "You are the planner for a team of AI agents. Break the user's task "
    "into 2-4 independent subtasks, each completable by one specialist "
    "agent that can research the web, search the user's documents, run "
    "Python, look at the screen, and generate images. Cover the whole "
    "task without overlap. Reply with ONLY the subtasks, one per line, "
    "no numbering or commentary."
)

WORKER_SYSTEM = (
    "You are a specialist agent on a team, responsible for one subtask "
    "of a larger job. Complete YOUR subtask only, using tools whenever "
    "they help (web_research for facts, run_python for computation, "
    "search_documents for the user's files). Be thorough but concise — "
    "your output goes to the team's reviewer, not the user."
)

REVIEWER_SYSTEM = (
    "You are the reviewer for a team of AI agents. Combine the workers' "
    "results into one final, well-organized answer to the user's task. "
    "Resolve contradictions, remove redundancy, keep citations and "
    "concrete numbers. Output ONLY the final answer."
)


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _plan(task: str) -> list[str]:
    response = ollama.chat(
        model=current_model(),
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": task},
        ],
    )
    lines = _strip_thinking(response["message"]["content"]).splitlines()
    subtasks = [line.strip(" -*0123456789.") for line in lines if line.strip()]
    return subtasks[:MAX_SUBTASKS] or [task]


def team_run(task: str):
    """Generator for the Team tab: yields live progress, then the
    combined final answer."""
    if not task.strip():
        yield "Describe a task first."
        return

    yield "*Planner is splitting up the task…*"
    subtasks = _plan(task)
    plan_log = ["**Team plan**"] + [
        f"{i + 1}. {subtask}" for i, subtask in enumerate(subtasks)
    ]

    results = []
    for i, subtask in enumerate(subtasks):
        yield "\n".join(
            plan_log + ["", f"*Agent {i + 1} of {len(subtasks)} working on: {subtask}…*"]
        )
        result = run_with_tools(
            WORKER_SYSTEM,
            f"Overall task: {task}\n\nYour subtask: {subtask}",
        )
        results.append(f"### {subtask}\n\n{result}")

    yield "\n".join(plan_log + ["", "*Reviewer is combining the results…*"])
    response = ollama.chat(
        model=current_model(),
        messages=[
            {"role": "system", "content": REVIEWER_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n\nWorker results:\n\n" + "\n\n".join(results)
                ),
            },
        ],
    )
    final = response["message"]["content"]
    yield "\n".join(plan_log) + "\n\n---\n\n" + final
