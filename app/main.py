"""
main.py — MomFlow AI pipeline orchestrator.

Wires together: STT → Extraction → Response Generation → Validation → Output.

Usage:
    # Audio file:
    python -m app.main --audio data/sample_audio/test.wav

    # Text input (for evals / debugging, no Whisper needed):
    python -m app.main --text "I need diapers size 4 and baby lotion next week"

    # Hindi text:
    python -m app.main --text "मुझे डायपर साइज 3 और बेबी लोशन चाहिए"

Exit codes:
    0 — pipeline completed (even refusals are a successful completion).
    1 — hard failure (file not found, API error, schema validation error).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Use relative imports when run as a module; absolute imports as a script
try:
    from .stt import transcribe, transcribe_text_passthrough
    from .extractor import extract_structure
    from .generator import generate_responses
    from .validator import safe_validate
except ImportError:
    from stt import transcribe, transcribe_text_passthrough
    from extractor import extract_structure
    from generator import generate_responses
    from validator import safe_validate


def run_pipeline(
    audio_path: str | Path | None = None,
    text: str | None = None,
    language_hint: str = "en",
) -> dict:
    """
    Execute the full MomFlow AI pipeline.

    Args:
        audio_path: Path to an audio file. Mutually exclusive with `text`.
        text:       Raw text input (bypasses STT). Mutually exclusive with `audio_path`.
        language_hint: Fallback language if STT cannot detect ('en' | 'hi').

    Returns:
        A dict that is either:
          • A validated MomFlowOutput serialised to dict (success).
          • An error dict with keys 'error', 'stage', 'detail' (failure).

    This function never raises — callers can always safely inspect the return value.
    """

    # ── Stage 1: Speech-to-Text ────────────────────────────────────────────
    try:
        if audio_path:
            transcript, detected_language = transcribe(audio_path)
        elif text:
            transcript, detected_language = transcribe_text_passthrough(
                text, language_hint
            )
        else:
            return {
                "error": "No input provided.",
                "stage": "input",
                "detail": "Pass either --audio or --text.",
            }
    except Exception as e:
        return {"error": str(e), "stage": "stt", "detail": type(e).__name__}

    # ── Stage 2: Structured Extraction ────────────────────────────────────
    try:
        extracted = extract_structure(transcript, detected_language)
    except Exception as e:
        return {"error": str(e), "stage": "extraction", "detail": type(e).__name__}

    # ── Stage 3: Bilingual Response Generation ────────────────────────────
    try:
        merged = generate_responses(extracted)
    except Exception as e:
        return {"error": str(e), "stage": "generation", "detail": type(e).__name__}

    # ── Stage 4: Schema Validation ────────────────────────────────────────
    result, errors = safe_validate(merged)

    if errors:
        return {
            "error": "Schema validation failed.",
            "stage": "validation",
            "detail": errors,
            "raw": merged,  # expose raw for debugging
        }

    return result.model_dump()


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MomFlow AI — Voice/Text → Structured Shopping List (EN + HI)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audio", help="Path to an audio file (.wav, .mp3, etc.)")
    group.add_argument("--text", help="Raw text input (bypasses STT)")
    parser.add_argument(
        "--lang",
        default="en",
        choices=["en", "hi"],
        help="Language hint for text mode (default: en)",
    )
    args = parser.parse_args()

    result = run_pipeline(
        audio_path=args.audio,
        text=args.text,
        language_hint=args.lang,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Return non-zero exit code on hard errors
    if "error" in result and result.get("stage") != "validation":
        sys.exit(1)


if __name__ == "__main__":
    main()