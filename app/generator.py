"""
generator.py — Bilingual response generator (English + Arabic).

Produces response_en and response_ar from the extracted structured data.

Design choices:
  • Arabic output is explicitly prompted to be written in natural Arabic
    register — NOT machine-translated English.
  • json_object mode is used when the provider supports it; otherwise the prompt
    enforces JSON-only output (free OpenRouter models).
"""

from __future__ import annotations

import json

from .config import llm_client as client, GENERATION_MODEL, SUPPORTS_JSON_OBJECT
from .extractor import CONFIDENCE_THRESHOLD

_RESPONSE_SYSTEM = """
You are MomFlow AI, a warm and helpful shopping assistant for Mumzworld.
You will receive structured data extracted from a mom's voice or text input.
Your job is to write two natural, friendly responses — one in English, one in Arabic.

CRITICAL RULES FOR ARABIC:
  • Write Arabic as a native Arabic speaker would — warm, concise, maternal tone.
  • DO NOT translate the English response word-for-word into Arabic.
  • Use natural Arabic sentence structure, not English structure in Arabic words.
  • Use common Arabic shopping expressions where appropriate.

CRITICAL RULES FOR ENGLISH:
  • Warm, concise, helpful tone — like a knowledgeable friend.
  • Summarise what was understood and any scheduled tasks.

Return ONLY this JSON object with no preamble, no markdown fences:
{"response_en": "<English response>", "response_ar": "<Arabic response>"}
"""

_REFUSAL_SYSTEM = """
You are MomFlow AI. The input was too vague, off-topic, or lacked enough detail.
Generate warm, helpful refusal messages in English and Arabic asking the user to clarify.

Arabic: natural Arabic register, maternal and warm.
English: friendly and encouraging.

Return ONLY this JSON object with no preamble, no markdown fences:
{"response_en": "<English refusal>", "response_ar": "<Arabic refusal>"}
"""


def _parse_json_response(raw: str) -> dict:
    """Parse JSON, stripping markdown fences if the model added them."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = [l for l in cleaned.split("\n") if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


def generate_responses(extracted: dict) -> dict:
    """
    Generate bilingual responses from the extracted structured data.
    Returns dict with response_en, response_ar, and refusal merged in.
    """
    confidence = extracted.get("confidence", 0.0)
    shopping_list = extracted.get("shopping_list", [])
    is_refusal = confidence < CONFIDENCE_THRESHOLD or not shopping_list

    if is_refusal:
        system = _REFUSAL_SYSTEM
        user_content = (
            f"Confidence: {confidence:.2f}\n"
            f"Shopping list: {shopping_list}\n"
            f"Original language: {extracted.get('language', 'en')}"
        )
    else:
        system = _RESPONSE_SYSTEM
        user_content = json.dumps(extracted, ensure_ascii=False, indent=2)

    kwargs: dict = dict(
        model=GENERATION_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
        max_tokens=600,
    )
    if SUPPORTS_JSON_OBJECT:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    raw = response.choices[0].message.content
    responses = _parse_json_response(raw)

    # Create clean result to avoid circular references
    result = {}
    
    # Copy basic fields from extracted
    for key in ["shopping_list", "schedule", "language", "confidence", "grounded"]:
        if key in extracted:
            result[key] = extracted[key]
    
    # Add RAG fields if present
    for key in ["grounded_items", "recommended_products", "unmatched_items", "grounding_score"]:
        if key in extracted:
            result[key] = extracted[key]
    
    # Add agent metadata if present
    if "agent_metadata" in extracted:
        result["agent_metadata"] = extracted["agent_metadata"]
    
    # Add response fields
    result.update(responses)
    result["refusal"] = responses["response_en"] if is_refusal else None
    
    return result