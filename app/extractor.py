"""
extractor.py — Core LLM extraction layer.

This module converts a raw transcript into a structured dict that matches
MomFlowOutput (minus response_en / response_ar, which are added by generator.py).

Architecture decisions:
  • We load the system prompt from a .txt file so prompt engineers can iterate
    without touching Python. The prompt is the most important artifact here.
  • We use json_object response_format (OpenAI feature) to guarantee the model
    returns parseable JSON — this eliminates the most common failure mode of
    markdown-fenced JSON.
  • Two-attempt retry: if the first parse fails (extremely rare with json_object
    mode), we send a self-repair message asking the model to fix its own output.
  • We NEVER fill in missing fields with defaults here; that's the validator's job.
  • The CONFIDENCE_THRESHOLD constant is the single place to tighten/loosen the
    uncertainty gate across the whole codebase.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import llm_client as client, EXTRACTION_MODEL, SUPPORTS_JSON_OBJECT

# Below this threshold, the pipeline will return a user-facing refusal
# instead of a potentially hallucinated shopping list.
CONFIDENCE_THRESHOLD = 0.50

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extraction_prompt.txt"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _call_llm(messages: list[dict], attempt: int = 1) -> str:
    """
    Single LLM call. Returns raw string content.

    Uses json_object mode when the provider supports it (OpenAI + paid OpenRouter).
    Falls back to prompt-level JSON enforcement for free OpenRouter models that
    don't support response_format — the extraction prompt already instructs JSON-only.
    """
    kwargs: dict = dict(
        model=EXTRACTION_MODEL,
        messages=messages,
        temperature=0.0,   # deterministic for eval reproducibility
        max_tokens=800,
    )
    if SUPPORTS_JSON_OBJECT:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def extract_structure(transcript: str, detected_language: str = "en") -> dict:
    """
    Extract structured shopping intent from a transcript.

    Args:
        transcript: Raw text from STT or a text-mode input.
        detected_language: Language code from Whisper ('en' | 'ar').

    Returns:
        A dict with keys: shopping_list, schedule, language, confidence, grounded.
        Does NOT contain response_en / response_ar (added by generator.py).

    The dict is intentionally unvalidated here; validation happens in validator.py
    after generator.py merges response fields in, ensuring one clean validation pass.
    """
    system_prompt = _load_system_prompt()

    # Hint the model about detected language so it doesn't have to guess
    user_message = (
        f"[Detected language hint: {detected_language}]\n\n"
        f"Mom's input:\n{transcript}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    raw = _call_llm(messages)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Self-repair: ask the model to return only valid JSON
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": (
                "Your response was not valid JSON. "
                "Return ONLY a valid JSON object with no extra text."
            ),
        })
        raw = _call_llm(messages, attempt=2)
        result = json.loads(raw)  # let this raise if it fails again

    # Safety: ensure required keys exist with safe defaults
    result.setdefault("shopping_list", [])
    result.setdefault("schedule", [])
    result.setdefault("language", detected_language)
    result.setdefault("confidence", 0.0)
    result.setdefault("grounded", False)

    return result