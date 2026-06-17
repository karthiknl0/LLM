"""Voice features: talk to the assistant and hear it answer, plus
transcription of any audio/video file.

Speech-to-text: faster-whisper (local). Text-to-speech: Kokoro (local,
needs the `espeak-ng` system package). Models load lazily on first use
and are kept around — they're small compared to the LLM.
"""

import datetime
import re

from app.chat.stream import stream_chat
from app.core.config import OUTPUTS_DIR, TTS_VOICE, WHISPER_MODEL

_whisper = None
_tts = None


def _get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel

        try:
            _whisper = WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")
        except Exception:
            _whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _whisper


def _get_tts():
    global _tts
    if _tts is None:
        from kokoro import KPipeline

        _tts = KPipeline(lang_code="a")  # American English
    return _tts


def transcribe(audio_path: str) -> list[tuple[float, str]]:
    """Return [(start_seconds, text), ...] segments for an audio/video file."""
    segments, _info = _get_whisper().transcribe(audio_path, vad_filter=True)
    return [(seg.start, seg.text.strip()) for seg in segments]


def speak(text: str) -> str | None:
    """Synthesize speech to a wav file; None if TTS is unavailable."""
    try:
        import numpy as np
        import soundfile as sf

        # keep clips reasonable and strip markdown decoration
        clean = re.sub(r"[*_#`>\[\]()]", " ", text)[:1500]
        chunks = [audio for _gs, _ps, audio in _get_tts()(clean, voice=TTS_VOICE)]
        if not chunks:
            return None
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = OUTPUTS_DIR / f"reply_{stamp}.wav"
        sf.write(str(out), np.concatenate(chunks), 24000)
        return str(out)
    except Exception as exc:
        print(f"[tts] unavailable: {exc} (is espeak-ng installed?)")
        return None


def voice_chat(audio_path: str | None):
    """Full voice turn: transcribe the mic recording, answer with the
    chat model (memory included), and speak the reply.
    Returns (your words, reply text, reply audio path)."""
    if not audio_path:
        return "No recording — press the mic button first.", "", None

    question = " ".join(text for _start, text in transcribe(audio_path)).strip()
    if not question:
        return "(couldn't hear anything — try again closer to the mic)", "", None

    reply = ""
    for reply in stream_chat(question, []):
        pass
    return question, reply, speak(reply)


def transcribe_file(file_path: str | None) -> str:
    """Timestamped transcript of an uploaded audio or video file."""
    if not file_path:
        return "Upload an audio or video file first."
    segments = transcribe(file_path)
    if not segments:
        return "No speech detected."
    lines = [
        f"[{int(start) // 60:02d}:{int(start) % 60:02d}] {text}"
        for start, text in segments
    ]
    return "\n".join(lines)
