"""
validator.py — Pydantic validation layer.

Called ONCE at the end of the pipeline after generator.py has merged all fields.
Failures are explicit: we raise ValidationError rather than returning partial data.

Design choice: validation is the last gate, not the first. This way:
  1. extractor.py handles LLM output quirks (missing keys, wrong types).
  2. generator.py fills in response_en / response_ar.
  3. validator.py then asserts the whole payload is schema-conformant.

If validation fails, main.py catches the error and returns a safe error dict
to the caller — never a partially filled MomFlowOutput.
"""

from __future__ import annotations

from pydantic import ValidationError

from .schema import MomFlowOutput


def validate_output(data: dict) -> MomFlowOutput:
    """
    Validate a merged dict against MomFlowOutput.

    Args:
        data: Merged dict from generator.py containing all required fields.

    Returns:
        A fully validated MomFlowOutput instance.

    Raises:
        pydantic.ValidationError: with field-level error detail if validation fails.
                                  The caller (main.py) is responsible for catching this
                                  and returning a user-friendly error.
    """
    return MomFlowOutput(**data)


def safe_validate(data: dict) -> tuple[MomFlowOutput | None, list[dict]]:
    """
    Validate without raising. Returns (result, errors).

    Useful in evals where we want to score partial outputs rather than crashing.

    Returns:
        Tuple of (MomFlowOutput or None, list of error dicts).
        If validation succeeds, errors is [].
        If validation fails, result is None and errors contains Pydantic's
        structured error list.
    """
    try:
        result = validate_output(data)
        return result, []
    except ValidationError as e:
        return None, e.errors()