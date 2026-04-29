"""
main.py — MomFlow AI pipeline orchestrator.

Wires together: STT → Extraction → Response Generation → Validation → Output.

Usage:
    # Audio file:
    python -m app.main --audio data/sample_audio/test.wav

    # Text input (for evals / debugging, no Whisper needed):
    python -m app.main --text "I need diapers size 4 and baby lotion next week"

    # Arabic text:
    python -m app.main --text "أحتاج حفاضات مقاس 3 وكريم الأطفال"

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
    from .agent import smart_refine, should_retry
    from .generator import generate_responses
    from .validator import safe_validate
    from .utils import check_confidence, validate_extraction_quality, generate_refusal_response, calculate_metrics
except ImportError:
    from stt import transcribe, transcribe_text_passthrough
    from agent import smart_refine, should_retry
    from generator import generate_responses
    from validator import safe_validate
    from utils import check_confidence, validate_extraction_quality, generate_refusal_response, calculate_metrics

# Import RAG module (always absolute due to directory structure)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from rag.retriever import ground_shopping_list, retrieve_products
from rag.reranker import rerank
from rag.vector_store import get_store

def run_pipeline(
    audio_path: str | Path | None = None,
    text: str | None = None,
    language_hint: str = "en",
    enable_agent_loop: bool = True,
    enable_rag: bool = True,
    enable_confidence_check: bool = True,
) -> dict:
    """
    Execute the advanced MomFlow AI pipeline with RAG, agent loop, and confidence-based rejection.

    Args:
        audio_path: Path to an audio file. Mutually exclusive with `text`.
        text:       Raw text input (bypasses STT). Mutually exclusive with `audio_path`.
        language_hint: Fallback language if STT cannot detect ('en' | 'ar').
        enable_agent_loop: Enable self-correction agent loop.
        enable_rag: Enable product retrieval and grounding.
        enable_confidence_check: Enable confidence-based rejection.

    Returns:
        A dict that is either:
          • A validated MomFlowOutput serialised to dict (success).
          • An error dict with keys 'error', 'stage', 'detail' (failure).
          • A rejection dict with keys 'status', 'message' (confidence-based rejection).

    This function never raises — callers can always safely inspect the return value.
    """
    
    # ── Initialize Vector Store with Caching ─────────────────────────────────
    if enable_rag:
        try:
            vector_store = get_store()
            if not vector_store.is_loaded:
                vector_store.load_data()
        except Exception as e:
            # Continue without RAG if vector store fails to initialize
            enable_rag = False
            print(f"Warning: Vector store initialization failed: {e}")

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

    # ── Stage 2: Agent-Enhanced Structured Extraction ────────────────────────
    try:
        if enable_agent_loop:
            # Use agent loop for self-correction
            extracted = smart_refine(transcript, detected_language)
        else:
            # Use basic extraction
            from .extractor import extract_structure
            extracted = extract_structure(transcript, detected_language)
    except Exception as e:
        return {"error": str(e), "stage": "extraction", "detail": type(e).__name__}

    # ── Stage 3: Confidence-Based Rejection Check ─────────────────────────
    if enable_confidence_check:
        confidence_check = check_confidence(extracted.get("confidence", 0.0))
        if confidence_check["status"] == "rejected":
            # Generate refusal responses
            refusal_responses = generate_refusal_response([confidence_check], detected_language)
            return {
                "status": "rejected",
                "reason": confidence_check["reason"],
                "message": confidence_check["message"],
                "confidence": extracted.get("confidence", 0.0),
                "threshold": confidence_check["threshold"],
                "response_en": refusal_responses["response_en"],
                "response_ar": refusal_responses["response_ar"],
                "stage": "confidence_check"
            }
    
    # ── Stage 4: Hybrid RAG Product Retrieval and Grounding ─────────────────────
    if enable_rag:
        try:
            grounding_result = ground_shopping_list(extracted.get("shopping_list", []))
            extracted.update(grounding_result)
            
            # ── Stage 4.5: LLM Re-ranking ─────────────────────────────────────
            if extracted.get("recommended_products"):
                try:
                    # Get the first item for re-ranking query
                    shopping_list = extracted.get("shopping_list", [])
                    if shopping_list:
                        query = shopping_list[0].get("item", "")
                        products = extracted["recommended_products"]
                        
                        # Apply LLM re-ranking
                        ranked_products = rerank(query, products, top_k=3)
                        extracted["recommended_products"] = ranked_products
                        extracted["reranking_applied"] = True
                        extracted["reranking_query"] = query
                except Exception as e:
                    # Continue without re-ranking if it fails
                    extracted["reranking_error"] = str(e)
                    extracted["reranking_applied"] = False
                    
        except Exception as e:
            # Continue without RAG if it fails
            extracted["grounding_score"] = 0.0
            extracted["recommended_products"] = []
            extracted["grounding_error"] = str(e)
    
    # ── Stage 5: Bilingual Response Generation ────────────────────────────
    try:
        merged = generate_responses(extracted)
    except Exception as e:
        return {"error": str(e), "stage": "generation", "detail": type(e).__name__}

    # ── Stage 6: Schema Validation ────────────────────────────────────────────
    result, errors = safe_validate(merged)

    if errors:
        return {
            "error": "Schema validation failed.",
            "stage": "validation",
            "detail": errors,
            "raw": merged,  # expose raw for debugging
        }
    
    # ── Stage 7: Performance Metrics Calculation ─────────────────────────────
    final_result = result.model_dump()
    if enable_rag or enable_agent_loop:
        metrics = calculate_metrics(final_result)
        final_result["metrics"] = metrics
    
    # ── Stage 8: Quality Validation ─────────────────────────────────────────────
    if enable_confidence_check:
        quality_assessment = validate_extraction_quality(final_result)
        final_result["quality_assessment"] = quality_assessment
        
        # Add quality score to metrics if not present
        if "metrics" not in final_result:
            final_result["metrics"] = {}
        final_result["metrics"]["quality_score"] = quality_assessment["quality_score"]

    return final_result


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MomFlow AI — Voice/Text → Structured Shopping List (EN + AR)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audio", help="Path to an audio file (.wav, .mp3, etc.)")
    group.add_argument("--text", help="Raw text input (bypasses STT)")
    parser.add_argument(
        "--lang",
        default="en",
        choices=["en", "ar"],
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