"""Web research: search the web, read the top results, and answer with
citations — like Perplexity, but the reasoning happens on your GPU.

This is the one feature that touches the internet (free DuckDuckGo
search + fetching public pages — no API keys, no accounts). Everything
else in the hub stays fully offline.
"""

import re
from concurrent.futures import ThreadPoolExecutor

import ollama

from app.config import CHAT_MODEL

MAX_SOURCES = 6
MAX_CHARS_PER_PAGE = 4000
DEEP_SUBQUERIES = 3
DEEP_MAX_SOURCES = 8


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _search(query: str) -> list[dict]:
    from ddgs import DDGS

    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=MAX_SOURCES))


def _fetch_page(url: str, fallback: str) -> str:
    """Clean article text from a URL; falls back to the search snippet."""
    try:
        import trafilatura

        html = trafilatura.fetch_url(url)
        text = trafilatura.extract(html) if html else None
        if text:
            return text[:MAX_CHARS_PER_PAGE]
    except Exception as exc:
        print(f"[research] could not read {url}: {exc}")
    return fallback


def research(question: str) -> str:
    """Search, read, and answer with [n] citations."""
    if not question.strip():
        return "Type a question first."

    try:
        results = _search(question)
    except Exception as exc:
        return f"Web search failed ({exc}). Are you online?"
    if not results:
        return "No search results found — try rephrasing."

    with ThreadPoolExecutor(max_workers=MAX_SOURCES) as pool:
        pages = list(
            pool.map(
                lambda r: _fetch_page(r["href"], r.get("body", "")), results
            )
        )

    context = "\n\n".join(
        f"[{i + 1}] {r['title']} ({r['href']})\n{page}"
        for i, (r, page) in enumerate(zip(results, pages))
    )
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a research assistant. Answer the question using "
                    "ONLY the numbered web sources provided. Cite sources "
                    "inline as [1], [2] etc. If the sources disagree, say so. "
                    "If they don't contain the answer, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Sources:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    answer = response["message"]["content"]

    source_list = "\n".join(
        f"{i + 1}. [{r['title']}]({r['href']})" for i, r in enumerate(results)
    )
    return f"{answer}\n\n---\n**Sources**\n{source_list}"


def _subqueries(question: str) -> list[str]:
    """Ask the LLM to attack the question from several search angles."""
    try:
        response = ollama.chat(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write {DEEP_SUBQUERIES} distinct web search queries "
                        f"that together would answer this question from "
                        f"different angles. One query per line, no numbering, "
                        f"nothing else.\n\nQuestion: {question}"
                    ),
                }
            ],
        )
        lines = _strip_thinking(response["message"]["content"]).splitlines()
        queries = [line.strip(" -*0123456789.") for line in lines if line.strip()]
        return queries[:DEEP_SUBQUERIES] or [question]
    except Exception:
        return [question]


def deep_research(question: str) -> str:
    """Slower, better: multiple search angles, more sources, and a
    verification pass before the final answer."""
    if not question.strip():
        return "Type a question first."

    seen, results = set(), []
    for query in [question] + _subqueries(question):
        try:
            for r in _search(query):
                if r["href"] not in seen:
                    seen.add(r["href"])
                    results.append(r)
        except Exception as exc:
            print(f"[research] search failed for '{query}': {exc}")
    results = results[:DEEP_MAX_SOURCES]
    if not results:
        return "No search results found. Are you online?"

    with ThreadPoolExecutor(max_workers=len(results)) as pool:
        pages = list(
            pool.map(lambda r: _fetch_page(r["href"], r.get("body", "")), results)
        )

    context = "\n\n".join(
        f"[{i + 1}] {r['title']} ({r['href']})\n{page}"
        for i, (r, page) in enumerate(zip(results, pages))
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful research assistant. Answer using ONLY "
                "the numbered web sources, citing them inline as [1], [2]. "
                "Note disagreements between sources. Say so if the sources "
                "don't contain the answer."
            ),
        },
        {
            "role": "user",
            "content": f"Sources:\n{context}\n\nQuestion: {question}",
        },
    ]
    draft = ollama.chat(model=CHAT_MODEL, messages=messages)["message"]["content"]

    # verification pass: check the draft against the sources
    messages += [
        {"role": "assistant", "content": draft},
        {
            "role": "user",
            "content": (
                "Verify your draft above against the sources: remove or "
                "correct any claim a cited source does not support, and add "
                "anything important you missed. Output ONLY the final "
                "answer with [n] citations."
            ),
        },
    ]
    answer = ollama.chat(model=CHAT_MODEL, messages=messages)["message"]["content"]

    source_list = "\n".join(
        f"{i + 1}. [{r['title']}]({r['href']})" for i, r in enumerate(results)
    )
    return f"{answer}\n\n---\n**Sources**\n{source_list}"
