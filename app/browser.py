"""In-browser verification: load a page in a headless browser,
screenshot it, and check it with the local vision model — so the agent
verifies web work by looking at it, not by assuming it works.

Needs: pip install playwright && python -m playwright install chromium
Degrades to a clear message when Playwright isn't installed.
"""

import datetime

from app.config import OUTPUTS_DIR
from app.vision import analyze_media

PAGE_TIMEOUT_MS = 30_000


def verify_in_browser(url: str, question: str = "") -> str:
    """Open a URL (http(s):// or file://), screenshot it, run the vision
    model over it, and report visible text and console errors."""
    url = (url or "").strip()
    if not url:
        return "Provide a URL (http://, https://, or file://)."

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return (
            "Playwright is not installed. Run: pip install playwright "
            "&& python -m playwright install chromium"
        )

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shot_path = OUTPUTS_DIR / f"page_{stamp}.png"
    console_errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text)
                if msg.type == "error"
                else None,
            )
            page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
            page.screenshot(path=str(shot_path))
            title = page.title()
            body_text = page.inner_text("body")[:800]
            browser.close()
    except Exception as exc:
        return f"Browser verification failed: {exc}"

    visual = analyze_media(
        str(shot_path),
        question or "Describe this web page. Note anything that looks broken, "
        "empty, misaligned, or like an error message.",
    )
    report = (
        f"Page title: {title}\n\n"
        f"Visual check (vision model): {visual}\n\n"
        f"Visible text (start): {body_text}"
    )
    if console_errors:
        report += "\n\nConsole errors:\n" + "\n".join(console_errors[:10])
    else:
        report += "\n\nConsole errors: none"
    return report + f"\n\n(screenshot saved to outputs/{shot_path.name})"
