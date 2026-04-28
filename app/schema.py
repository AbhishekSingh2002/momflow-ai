"""
schema.py — Pydantic models for MomFlow AI structured output.

Every field is intentionally typed. Optional fields must be explicitly None
rather than missing so downstream validators can distinguish "not provided"
from "field not in schema". confidence drives uncertainty gating throughout
the pipeline: if confidence < CONFIDENCE_THRESHOLD, the pipeline will return
a graceful refusal rather than a low-quality structured result.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────
# Leaf models
# ──────────────────────────────────────────────

class Item(BaseModel):
    """A single shopping item extracted from the voice/text input."""

    item: str = Field(..., description="Product name in the input language")
    details: Optional[str] = Field(
        None,
        description="Qualifier such as size, brand, quantity, or variant. "
                    "Must be null if the user did not mention one — never invent.",
    )
    quantity: Optional[int] = Field(
        None,
        description="Numeric quantity if explicitly stated, else null.",
        ge=1,
    )


class ScheduleEntry(BaseModel):
    """A time-bound task derived from the input."""

    task: str = Field(..., description="Short imperative task description.")
    date: str = Field(
        ...,
        description="Human-readable date or relative expression "
                    "(e.g. 'tomorrow', 'next week', '2025-08-10').",
    )


# ──────────────────────────────────────────────
# Root model
# ──────────────────────────────────────────────

class MomFlowOutput(BaseModel):
    """
    Full validated output of the MomFlow AI pipeline.

    Fields:
        shopping_list   — extracted items; empty list if none found.
        schedule        — time-bound tasks; empty list if none implied.
        language        — detected primary language code ('en' | 'ar' | 'other').
        confidence      — [0, 1] float. Values below 0.5 indicate the model
                          was uncertain; the pipeline should surface a refusal
                          rather than a potentially wrong list.
        grounded        — True when every item in shopping_list maps directly
                          to something the user said. False if the model
                          inferred/guessed an item not stated.
        refusal         — Non-null when confidence < threshold or input is
                          out-of-scope. Contains a user-facing message.
        response_en     — Natural English reply summarising the list + schedule.
        response_ar     — Natural Arabic reply (not a translation; rewritten
                          for Arabic register and word order).
    """

    shopping_list: List[Item] = Field(default_factory=list)
    schedule: List[ScheduleEntry] = Field(default_factory=list)
    language: str = Field(..., description="'en', 'ar', or 'other'.")
    confidence: float = Field(..., ge=0.0, le=1.0)
    grounded: bool = Field(
        ...,
        description="True only when every extracted item was explicitly stated.",
    )
    refusal: Optional[str] = Field(
        None,
        description="User-facing message when the model cannot confidently answer.",
    )
    response_en: str = Field(..., description="English-language reply.")
    response_ar: str = Field(..., description="Arabic-language reply.")

    # ── validators ──────────────────────────────

    @field_validator("language")
    @classmethod
    def language_must_be_known(cls, v: str) -> str:
        allowed = {"en", "ar", "other"}
        if v not in allowed:
            raise ValueError(f"language must be one of {allowed}, got '{v}'")
        return v

    @field_validator("response_ar")
    @classmethod
    def arabic_must_not_be_placeholder(cls, v: str) -> str:
        if v.strip() in {"", "N/A", "None", "null"}:
            raise ValueError(
                "response_ar must be a real Arabic string, not a placeholder."
            )
        return v