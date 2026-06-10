"""Look at the screen: capture this computer's display and analyze it
with the local vision model. Nothing leaves the machine — the capture
happens on the desktop running the app.
"""

import datetime

from app.config import OUTPUTS_DIR
from app.vision import analyze_media

DEFAULT_QUESTION = "Describe what is on the screen."


def capture_screen() -> str | None:
    """Screenshot the primary monitor; returns the PNG path, or None if
    capture isn't possible (no display, mss missing)."""
    try:
        import mss
        import mss.tools

        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[1])
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = OUTPUTS_DIR / f"screen_{stamp}.png"
            mss.tools.to_png(shot.rgb, shot.size, output=str(path))
            return str(path)
    except Exception as exc:
        print(f"[screen] capture failed: {exc}")
        return None


def look_at_screen(question: str = "") -> str:
    """Agent tool: capture the screen and answer a question about it."""
    path = capture_screen()
    if not path:
        return (
            "Could not capture the screen — the app must be running on a "
            "desktop with a display (not headless/remote)."
        )
    return analyze_media(path, question or DEFAULT_QUESTION)


def capture_and_analyze(question: str):
    """For the Screen tab: returns (screenshot path, analysis)."""
    path = capture_screen()
    if not path:
        return None, "Could not capture the screen — is the app running on this desktop?"
    return path, analyze_media(path, question or DEFAULT_QUESTION)
