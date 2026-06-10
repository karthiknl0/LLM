"""Build the training dataset from your chat logs and custom examples.

Run:  python -m finetune.export_data

Sources:
  data/chatlogs/*.jsonl   — logged automatically while you chat
  data/training/custom*.jsonl — examples you write yourself, either as
      {"user": "...", "assistant": "..."} or {"messages": [...]}

Output: data/training/dataset.jsonl, one {"messages": [...]} per line.
"""

import json

from finetune.config import CHATLOG_DIR, MIN_EXAMPLES, SYSTEM_PROMPT, TRAINING_DIR


def _to_messages(record: dict) -> list[dict] | None:
    if "messages" in record:
        return record["messages"]
    if "user" in record and "assistant" in record:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": record["user"]},
            {"role": "assistant", "content": record["assistant"]},
        ]
    return None


def _load_jsonl(path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"[export] bad line skipped in {path.name}")
    return records


def main() -> None:
    sources = sorted(CHATLOG_DIR.glob("*.jsonl"))
    sources += sorted(TRAINING_DIR.glob("custom*.jsonl"))

    examples, seen = [], set()
    for path in sources:
        for record in _load_jsonl(path):
            messages = _to_messages(record)
            if not messages:
                continue
            key = json.dumps(messages, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            examples.append({"messages": messages})

    out = TRAINING_DIR / "dataset.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"Wrote {len(examples)} examples to {out}")
    if len(examples) < MIN_EXAMPLES:
        print(
            f"WARNING: fewer than {MIN_EXAMPLES} examples. Keep chatting "
            "(or add custom*.jsonl files) before training — tiny datasets "
            "make the model worse, not better."
        )


if __name__ == "__main__":
    main()
