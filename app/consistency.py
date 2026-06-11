"""Self-consistency voting (Wang et al., 2022): for a reasoning
question, sample several independent answers at higher temperature and
return the one the model agrees on most. Trades time for accuracy on
math/logic — an inference-time way to get more reliable answers from
the same model.
"""

import re
from collections import Counter

import ollama

from app.modelstate import current_model

DEFAULT_SAMPLES = 5

ANSWER_SYSTEM = (
    "Solve the problem. Think step by step, then end with a line in "
    "exactly this form:\nFINAL: <your concise final answer>"
)


def _final_line(text: str) -> str | None:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    matches = re.findall(r"FINAL:\s*(.+)", text)
    if not matches:
        return None
    return matches[-1].strip().rstrip(".").strip().lower()


def self_consistency(question: str, samples: int = DEFAULT_SAMPLES) -> str:
    """Sample `samples` answers and return the majority one with a tally."""
    if not (question or "").strip():
        return "Ask a question to vote on."
    answers, raw_by_answer = [], {}
    for _ in range(max(2, samples)):
        try:
            response = ollama.chat(
                model=current_model(),
                messages=[
                    {"role": "system", "content": ANSWER_SYSTEM},
                    {"role": "user", "content": question},
                ],
                options={"temperature": 0.8},
            )
        except Exception as exc:
            return f"Voting failed: {exc}"
        text = response["message"]["content"]
        final = _final_line(text)
        if final:
            answers.append(final)
            raw_by_answer.setdefault(final, text.strip())

    if not answers:
        return "No FINAL: answer was produced — try a clearer question."

    tally = Counter(answers)
    winner, votes = tally.most_common(1)[0]
    breakdown = ", ".join(f"{a!r}×{c}" for a, c in tally.most_common())
    confidence = 100 * votes / len(answers)
    return (
        f"**Majority answer ({votes}/{len(answers)}, {confidence:.0f}% agree):** "
        f"{winner}\n\n_Vote spread: {breakdown}_"
    )
