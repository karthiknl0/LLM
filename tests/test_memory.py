import sys
from types import SimpleNamespace

sys.modules.setdefault(
    "chromadb",
    SimpleNamespace(PersistentClient=lambda **_kwargs: object()),
)

import app.memory.store as memory


def test_generic_greetings_do_not_recall_unrelated_memory(monkeypatch):
    calls = []

    def fake_recall(collection, query, k):
        calls.append((collection, query, k))
        return ["old project"]

    monkeypatch.setattr(memory, "_recall_from", fake_recall)

    assert memory.recall("hi") == []
    assert memory.recall_lessons("Good morning!") == []
    assert calls == []

    assert memory.recall("open the omshakthisilks project") == ["old project"]
    assert calls == [
        (memory.FACTS_COLLECTION, "open the omshakthisilks project", 5)
    ]
