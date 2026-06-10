"""Image and video understanding with a local vision model."""

import tempfile
from pathlib import Path

import cv2
import ollama

from app.config import VIDEO_FRAMES_TO_SAMPLE, VISION_MODEL

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}


def _ask_vision(prompt: str, image_paths: list[str]) -> str:
    response = ollama.chat(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": prompt, "images": image_paths}],
    )
    return response["message"]["content"]


def _sample_video_frames(video_path: str) -> tuple[list[str], float]:
    """Save evenly-spaced frames to temp files; return paths and duration."""
    capture = cv2.VideoCapture(video_path)
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30
    duration = total / fps if total else 0

    count = min(VIDEO_FRAMES_TO_SAMPLE, max(total, 1))
    indices = [int(i * (max(total - 1, 0)) / max(count - 1, 1)) for i in range(count)]

    frame_paths = []
    tmpdir = Path(tempfile.mkdtemp(prefix="frames_"))
    for n, index in enumerate(indices):
        capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = capture.read()
        if not ok:
            continue
        out = tmpdir / f"frame_{n:02d}.jpg"
        cv2.imwrite(str(out), frame)
        frame_paths.append(str(out))
    capture.release()
    return frame_paths, duration


def analyze_media(file_path: str, question: str) -> str:
    """Answer a question about an image or a video file."""
    if not file_path:
        return "Upload an image or video first."
    question = question.strip() or "Describe this in detail."

    if Path(file_path).suffix.lower() in VIDEO_EXTENSIONS:
        frames, duration = _sample_video_frames(file_path)
        if not frames:
            return "Could not read any frames from this video."
        prompt = (
            f"These are {len(frames)} frames sampled evenly from a "
            f"{duration:.0f}-second video, in order. Treat them as one "
            f"video, not separate pictures. {question}"
        )
        return _ask_vision(prompt, frames)

    return _ask_vision(question, [file_path])
