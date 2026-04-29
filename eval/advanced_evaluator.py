"""
eval/advanced_evaluator.py — Advanced Evaluation System for Next-Level MomFlow

Evaluates the enhanced pipeline with:
- RAG grounding accuracy
- Agent loop effectiveness  
- Confidence-based rejection correctness
- Performance metrics
- Quality assessment
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    """Result of evaluating a single test case."""
    case_id: str
    total_score: float
    max_score: float
    percentage: float
    details: Dict[str, Any]
    passed: bool

class AdvancedEvaluator:
    """Advanced evaluator for next-level MomFlow AI features."""
    
    def __init__(self):
        self.test_cases = self._load_test_cases()
        self.results = []
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases from JSON file."""
        try:
            test_cases_path = Path(__file__).parent.parent / "data" / "test_cases.json"
            with open(test_cases_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("Test cases file not found")
    
    def evaluate_all(self) -> Dict[str, Any]:
        """Evaluate all test cases and return comprehensive results."""
        print("🧠 Advanced MomFlow AI Evaluation")
        print("=" * 60)
        
        total_score = 0
        max_total_score = 0
        
        for case in self.test_cases:
            result = self._evaluate_case(case)
            self.results.append(result)
            
            total_score += result.total_score
            max_total_score += result.max_score
            
            self._print_case_result(result)
        
        # Calculate overall metrics
        overall_percentage = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        print("\n" + "=" * 60)
        print(f"📊 OVERALL SCORE: {total_score}/{max_total_score} ({overall_percentage:.1f}%)")
        print("=" * 60)
        
        # Generate detailed report
        report = self._generate_report(total_score, max_total_score, overall_percentage)
        
        return report
    
    def _evaluate_case(self, case: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a single test case."""
        from app.main import run_pipeline
        
        case_id = case["id"]
        description = case["description"]
        input_text = case["input"]
        language_hint = case.get("language_hint", "en")
        
        print(f"\n[{case_id}] {description}")
        print(f"  Input: {input_text[:50]}{'...' if len(input_text) > 50 else ''}")
        
        try:
            # Run the advanced pipeline
            result = run_pipeline(
                text=input_text,
                language_hint=language_hint,
                enable_agent_loop=True,
                enable_rag=True,
                enable_confidence_check=True
            )
            
            # Check if it was rejected
            if result.get("status") == "rejected":
                return self._evaluate_rejection(case, result)
            
            # Evaluate successful extraction
            return self._evaluate_success(case, result)
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            return EvaluationResult(
                case_id=case_id,
                total_score=0,
                max_score=10,
                percentage=0.0,
                details={"error": str(e)},
                passed=False
            )
    
    def _evaluate_success(self, case: Dict[str, Any], result: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a successful extraction result."""
        score = 0
        max_score = 10
        details = {}
        
        # 1. Basic extraction accuracy (3 points)
        expected_items = case.get("expected_items", [])
        actual_items = [item["item"] for item in result.get("shopping_list", [])]
        
        if expected_items:
            item_match = any(expected.lower() in " ".join(actual_items).lower() for expected in expected_items)
            if item_match:
                score += 3
                details["extraction_accuracy"] = "✅ Items extracted correctly"
            else:
                details["extraction_accuracy"] = "❌ Items not found"
        else:
            # Expected empty list
            if not actual_items:
                score += 3
                details["extraction_accuracy"] = "✅ Correctly returned empty list"
            else:
                details["extraction_accuracy"] = "❌ Should have returned empty list"
        
        # 2. RAG grounding accuracy (2 points)
        grounding_score = result.get("grounding_score", 0.0)
        recommended_products = result.get("recommended_products", [])
        
        if grounding_score >= 0.7:
            score += 2
            details["rag_grounding"] = f"✅ Excellent grounding ({grounding_score:.2f})"
        elif grounding_score >= 0.5:
            score += 1
            details["rag_grounding"] = f"⚠️  Moderate grounding ({grounding_score:.2f})"
        else:
            details["rag_grounding"] = f"❌ Poor grounding ({grounding_score:.2f})"
        
        # 3. Agent loop effectiveness (2 points)
        agent_metadata = result.get("agent_metadata", {})
        if agent_metadata.get("self_corrected"):
            score += 2
            details["agent_loop"] = f"✅ Self-corrected ({agent_metadata.get('total_attempts', 0)} attempts)"
        elif agent_metadata.get("total_attempts", 1) == 1:
            score += 1
            details["agent_loop"] = "⚠️  Single attempt (no correction needed)"
        else:
            details["agent_loop"] = "❌ Agent loop failed"
        
        # 4. Confidence appropriateness (2 points)
        confidence = result.get("confidence", 0.0)
        expected_confidence_range = case.get("expected_confidence_range", [0.5, 1.0])
        
        if expected_confidence_range[0] <= confidence <= expected_confidence_range[1]:
            score += 2
            details["confidence"] = f"✅ Appropriate confidence ({confidence:.2f})"
        else:
            details["confidence"] = f"❌ Inappropriate confidence ({confidence:.2f})"
        
        # 5. Quality assessment (1 point)
        quality_assessment = result.get("quality_assessment", {})
        quality_score = quality_assessment.get("quality_score", 0.0)
        
        if quality_score >= 0.8:
            score += 1
            details["quality"] = f"✅ High quality ({quality_score:.2f})"
        else:
            details["quality"] = f"⚠️  Quality issues ({quality_score:.2f})"
        
        passed = score >= (max_score * 0.6)  # 60% to pass
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status} Score: {score}/{max_score}")
        
        for key, value in details.items():
            print(f"     {key}: {value}")
        
        return EvaluationResult(
            case_id=case["id"],
            total_score=score,
            max_score=max_score,
            percentage=(score / max_score * 100),
            details=details,
            passed=passed
        )
    
    def _evaluate_rejection(self, case: Dict[str, Any], result: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a confidence-based rejection."""
        score = 0
        max_score = 10
        details = {}
        
        expected_rejection = case.get("expect_refusal", False)
        
        if expected_rejection:
            score += 5
            details["rejection_correctness"] = "✅ Correctly rejected ambiguous input"
            
            # Check confidence threshold
            confidence = result.get("confidence", 0.0)
            threshold = result.get("threshold", 0.5)
            
            if confidence < threshold:
                score += 3
                details["confidence_threshold"] = f"✅ Proper low confidence ({confidence:.2f} < {threshold})"
            else:
                details["confidence_threshold"] = f"❌ Confidence too high ({confidence:.2f} >= {threshold})"
            
            # Check response quality
            response_en = result.get("response_en", "")
            response_ar = result.get("response_ar", "")
            
            if response_en and "more specific" in response_en.lower():
                score += 2
                details["response_quality"] = "✅ Helpful rejection message"
            else:
                details["response_quality"] = "⚠️  Rejection message could be better"
        else:
            details["rejection_correctness"] = "❌ Incorrectly rejected valid input"
        
        passed = score >= (max_score * 0.6)
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status} Score: {score}/{max_score} (Rejection)")
        
        for key, value in details.items():
            print(f"     {key}: {value}")
        
        return EvaluationResult(
            case_id=case["id"],
            total_score=score,
            max_score=max_score,
            percentage=(score / max_score * 100),
            details=details,
            passed=passed
        )
    
    def _print_case_result(self, result: EvaluationResult):
        """Print the result of a single test case."""
        if result.passed:
            print(f"  ✅ Score: {result.total_score}/{result.max_score}")
        else:
            print(f"  ❌ Score: {result.total_score}/{result.max_score}")
    
    def _generate_report(self, total_score: float, max_total_score: float, percentage: float) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        passed_cases = sum(1 for r in self.results if r.passed)
        total_cases = len(self.results)
        
        # Calculate category scores
        categories = {
            "extraction_accuracy": [],
            "rag_grounding": [],
            "agent_loop": [],
            "confidence": [],
            "quality": []
        }
        
        for result in self.results:
            for category in categories.keys():
                if category in result.details:
                    # Extract score from detail (simplified)
                    if "✅" in result.details[category]:
                        categories[category].append(1.0)
                    elif "⚠️" in result.details[category]:
                        categories[category].append(0.5)
                    else:
                        categories[category].append(0.0)
        
        category_averages = {}
        for category, scores in categories.items():
            category_averages[category] = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "overall_score": total_score,
            "max_score": max_total_score,
            "percentage": percentage,
            "cases_passed": passed_cases,
            "total_cases": total_cases,
            "pass_rate": (passed_cases / total_cases * 100) if total_cases > 0 else 0,
            "category_performance": category_averages,
            "detailed_results": [
                {
                    "case_id": r.case_id,
                    "score": r.total_score,
                    "max_score": r.max_score,
                    "percentage": r.percentage,
                    "passed": r.passed,
                    "details": r.details
                }
                for r in self.results
            ]
        }

def run_advanced_evaluation():
    """Run the advanced evaluation system."""
    evaluator = AdvancedEvaluator()
    return evaluator.evaluate_all()

if __name__ == "__main__":
    run_advanced_evaluation()
