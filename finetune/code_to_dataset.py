"""Turn a codebase into fine-tuning data: walk a folder of source files
and build Q&A-style examples that teach the model your code's patterns
and conventions. The local model writes a realistic instruction for
each code chunk; the chunk is the target answer.

Run:  python -m finetune.code_to_dataset /path/to/your/project

Output is appended to data/training/custom_code.jsonl, which
export_data.py then folds into the training set. Honest note: this
teaches the model to imitate THIS code's style and idioms — it does not
add general coding IQ, which is set by the base model.
"""

import json
import sys
from pathlib import Path

import ollama

from finetune.config import CHAT_MODEL_FOR_DATAGEN, SYSTEM_PROMPT, TRAINING_DIR

CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c",
    ".cpp", ".h", ".rb", ".php", ".cs", ".swift", ".kt", ".sql",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
MAX_CHUNK_LINES = 60
MIN_CHUNK_LINES = 5

INSTRUCTION_PROMPT = (
    "Below is a snippet from a real codebase. Write ONE concise developer "
    "instruction that this snippet would be the correct answer to (e.g. "
    "'Write a function that …', 'Add a Gradio tab that …'). Reply with the "
    "instruction only, no preamble.\n\n```\n{code}\n```"
)


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in CODE_EXTS:
            if not (set(path.parts) & SKIP_DIRS):
                yield path


def _chunks(text: str):
    lines = text.splitlines()
    for start in range(0, len(lines), MAX_CHUNK_LINES):
        block = lines[start : start + MAX_CHUNK_LINES]
        if len(block) >= MIN_CHUNK_LINES:
            yield "\n".join(block)


def _instruction_for(code: str) -> str | None:
    try:
        response = ollama.chat(
            model=CHAT_MODEL_FOR_DATAGEN,
            messages=[{"role": "user", "content": INSTRUCTION_PROMPT.format(code=code[:3000])}],
        )
        text = response["message"]["content"].strip().strip('"')
        return text or None
    except Exception as exc:
        print(f"[code2data] instruction generation failed: {exc}")
        return None


def main(root_arg: str) -> None:
    root = Path(root_arg).expanduser()
    if not root.is_dir():
        raise SystemExit(f"Not a folder: {root}")

    out = TRAINING_DIR / "custom_code.jsonl"
    written = 0
    with out.open("a", encoding="utf-8") as f:
        for path in _iter_files(root):
            lang = path.suffix.lstrip(".")
            for code in _chunks(path.read_text(encoding="utf-8", errors="replace")):
                instruction = _instruction_for(code)
                if not instruction:
                    continue
                example = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": instruction},
                        {"role": "assistant", "content": f"```{lang}\n{code}\n```"},
                    ]
                }
                f.write(json.dumps(example, ensure_ascii=False) + "\n")
                written += 1
            print(f"  {path.name}: {written} examples so far")

    print(
        f"\nWrote {written} examples to {out}\n"
        "Next: python -m finetune.export_data  (folds this in)\n"
        "Then: python -m finetune.train"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m finetune.code_to_dataset /path/to/project")
    main(sys.argv[1])
