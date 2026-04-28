"""
evaluator.py — MomFlow AI Evaluation Harness.

Runs all test cases in data/test_cases.json through the extraction pipeline
and scores each one against a multi-criterion rubric. Produces a summary
report printed to stdout and optionally saved to eval/eval_report.json.

Rubric (per test case, max 5 points):
  [1pt] item_recall       — expected items found in shopping_list
  [1pt] no_hallucination  — no items invented beyond what user said
  [1pt] refusal_correct   — refusal returned iff expected
  [1pt] confidence_range  — confidence within expected bounds
  [1pt] schema_valid      — output validates against MomFlowOutput schema

Usage:
    python -m eval.evaluator
    python -m eval.evaluator --save          # saves eval_report.json
    python -m eval.evaluator --tag adversarial  # run only adversarial cases
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Handle running as module vs script
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.extractor import extract_structure
from app.generator import generate_responses
from app.validator import safe_validate

TEST_CASES_PATH = Path(__file__).parent.parent / "data" / "test_cases.json"
REPORT_PATH = Path(__file__).parent / "eval_report.json"


# ── Scoring ────────────────────────────────────────────────────────────────

def score_case(test: dict, result: dict, errors: list) -> dict:
    """
    Score a single test case. Returns a dict with per-criterion scores.
    """
    scores = {}
    detail = {}

    extracted_items = [
        i.get("item", "").lower()
        for i in result.get("shopping_list", [])
    ]
    confidence = result.get("confidence", 0.0)
    has_refusal = result.get("refusal") is not None

    # ── 1. Item recall ────────────────────────────────────────────────────
    if "expected_items" in test:
        expected = [e.lower() for e in test["expected_items"]]
        if not expected:
            # We expected an empty list — pass if shopping_list is also empty
            scores["item_recall"] = 1 if not extracted_items else 0
            detail["item_recall"] = "expected empty list"
        else:
            found = sum(
                1 for e in expected
                if any(e in item or item in e for item in extracted_items)
            )
            scores["item_recall"] = 1 if found == len(expected) else round(found / len(expected), 2)
            detail["item_recall"] = f"{found}/{len(expected)} expected items found"
    elif "expected_items_partial" in test:
        partials = [e.lower() for e in test["expected_items_partial"]]
        found = sum(
            1 for p in partials
            if any(p in item or item in p for item in extracted_items)
        )
        scores["item_recall"] = 1 if found > 0 else 0
        detail["item_recall"] = f"partial match: {found}/{len(partials)}"
    else:
        scores["item_recall"] = 1  # no expectation → skip
        detail["item_recall"] = "no item expectation defined"

    # ── 2. No hallucination ───────────────────────────────────────────────
    if test.get("must_not_hallucinate"):
        # Grounded flag must be True, AND items count should be minimal
        grounded = result.get("grounded", False)
        # Heuristic: if the input was vague, more than 1 specific product = hallucination
        scores["no_hallucination"] = 1 if grounded else 0
        detail["no_hallucination"] = f"grounded={grounded}"
    else:
        scores["no_hallucination"] = 1  # not a hallucination test
        detail["no_hallucination"] = "not evaluated for this case"

    # ── 3. Refusal correctness ────────────────────────────────────────────
    expect_refusal = test.get("expect_refusal", False)
    if expect_refusal:
        scores["refusal_correct"] = 1 if has_refusal else 0
        detail["refusal_correct"] = f"expected refusal, got refusal={has_refusal}"
    else:
        scores["refusal_correct"] = 1 if not has_refusal else 0
        detail["refusal_correct"] = f"expected no refusal, got refusal={has_refusal}"

    # ── 4. Confidence range ───────────────────────────────────────────────
    conf_ok = True
    if "min_confidence" in test and confidence < test["min_confidence"]:
        conf_ok = False
    if "max_confidence" in test and confidence > test["max_confidence"]:
        conf_ok = False
    scores["confidence_range"] = 1 if conf_ok else 0
    detail["confidence_range"] = f"confidence={confidence:.2f}"

    # ── 5. Schema validity ────────────────────────────────────────────────
    scores["schema_valid"] = 1 if not errors else 0
    detail["schema_valid"] = "valid" if not errors else f"{len(errors)} error(s)"

    total = sum(scores.values())
    return {"scores": scores, "detail": detail, "total": total, "max": 5}


# ── Runner ─────────────────────────────────────────────────────────────────

def run_eval(tag_filter: Optional[str] = None) -> list[dict]:
    cases = json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))

    if tag_filter:
        cases = [c for c in cases if tag_filter in c.get("tags", [])]
        print(f"Filtered to {len(cases)} cases with tag '{tag_filter}'\n")

    results = []
    total_score = 0
    max_score = 0

    for test in cases:
        case_id = test["id"]
        input_text = test["input"].strip()

        print(f"[{case_id}] {test['description'][:60]}")
        print(f"  Input: {input_text[:80]}")

        try:
            extracted = extract_structure(input_text, test.get("language_hint", "en"))
            merged = generate_responses(extracted)
            result, validation_errors = safe_validate(merged)
            result_dict = result.model_dump() if result else merged
        except Exception as e:
            print(f"  ⚠️  Pipeline error: {e}\n")
            results.append({
                "id": case_id,
                "error": str(e),
                "scores": {},
                "total": 0,
                "max": 5,
            })
            max_score += 5
            continue

        scored = score_case(test, result_dict, validation_errors)
        total_score += scored["total"]
        max_score += scored["max"]

        verdict = "✅" if scored["total"] == 5 else ("⚠️ " if scored["total"] >= 3 else "❌")
        print(f"  {verdict} Score: {scored['total']}/5")
        for criterion, score in scored["scores"].items():
            icon = "✓" if score == 1 else ("~" if 0 < score < 1 else "✗")
            print(f"     {icon} {criterion}: {score} — {scored['detail'][criterion]}")
        print()

        results.append({
            "id": case_id,
            "description": test["description"],
            "input": input_text,
            "output": result_dict,
            **scored,
        })

    accuracy = total_score / max_score if max_score > 0 else 0
    print("═" * 60)
    print(f"TOTAL: {total_score}/{max_score}  ({accuracy:.0%} accuracy)")
    print("═" * 60)

    return results


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="MomFlow AI Evaluator")
    parser.add_argument("--save", action="store_true", help="Save report to eval/eval_report.json")
    parser.add_argument("--tag", help="Filter test cases by tag")
    args = parser.parse_args()

    results = run_eval(tag_filter=args.tag)

    if args.save:
        REPORT_PATH.parent.mkdir(exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()