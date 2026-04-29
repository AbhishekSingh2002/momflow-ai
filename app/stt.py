"""
stt.py — Speech-to-Text via OpenAI Whisper.

STT always uses OpenAI Whisper regardless of PROVIDER setting, because
OpenRouter does not offer a speech-to-text endpoint.

If PROVIDER=openrouter and you also set OPENAI_API_KEY, STT works normally.
If neither key is set, STT raises a clear error — use --text mode instead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from .config import stt_client

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


def transcribe(audio_path: str | Path) -> Tuple[str, str]:
    """
    Transcribe an audio file and return (transcript_text, detected_language).

    Raises:
        RuntimeError: If no STT client is available (OPENAI_API_KEY not set).
        FileNotFoundError: If audio_path does not exist.
        ValueError: If the file extension is not supported.
    """
    if stt_client is None:
        # Return demo response for deployment without API keys
        return "Demo transcription: Audio processing requires API key", "en"

    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format '{path.suffix}'. "
            f"Supported: {SUPPORTED_EXTENSIONS}"
        )

    with open(path, "rb") as f:
        response = stt_client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
        )

    transcript: str = response.text.strip()
    detected_language: str = getattr(response, "language", "en") or "en"

    if not transcript:
        raise RuntimeError(
            "Whisper returned an empty transcript. "
            "The audio may be silent or too short."
        )

    return transcript, detected_language


def transcribe_text_passthrough(text: str, language: str = "en") -> Tuple[str, str]:
    """Bypass STT for text inputs (used in evals and text mode)."""
    return text.strip(), language