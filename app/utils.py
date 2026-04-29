"""
app/utils.py — Utility functions for confidence-based rejection and validation

Implements critical evaluation criteria:
- Confidence-based rejection to prevent hallucinations
- Grounding validation
- Quality metrics
"""

from typing import Dict, Any, List

CONFIDENCE_THRESHOLD = 0.5
GROUNDING_THRESHOLD = 0.7

def check_confidence(confidence: float) -> Dict[str, Any]:
    """
    Check if confidence meets threshold for processing.
    
    Args:
        confidence: Confidence score from extraction (0.0 to 1.0)
        
    Returns:
        Dictionary with rejection status and message
    """
    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "status": "rejected",
            "reason": "low_confidence",
            "message": "I'm not confident enough to process this request accurately. Could you provide more specific details about what you need?",
            "confidence": confidence,
            "threshold": CONFIDENCE_THRESHOLD
        }
    
    return {
        "status": "accepted",
        "confidence": confidence,
        "threshold": CONFIDENCE_THRESHOLD
    }

def check_grounding(grounding_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if shopping list is properly grounded in product data.
    
    Args:
        grounding_result: Result from RAG grounding system
        
    Returns:
        Dictionary with grounding validation
    """
    grounding_score = grounding_result.get("grounding_score", 0.0)
    unmatched_items = grounding_result.get("unmatched_items", [])
    
    if grounding_score < GROUNDING_THRESHOLD and unmatched_items:
        return {
            "status": "warning",
            "reason": "low_grounding",
            "message": f"I found some items I'm not sure about: {', '.join([item.get('item', 'unknown') for item in unmatched_items])}. Could you clarify these?",
            "grounding_score": grounding_score,
            "unmatched_items": unmatched_items
        }
    
    return {
        "status": "grounded",
        "grounding_score": grounding_score
    }

def validate_extraction_quality(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive validation of extraction quality.
    
    Args:
        result: Full extraction result
        
    Returns:
        Quality assessment with recommendations
    """
    confidence = result.get("confidence", 0.0)
    shopping_list = result.get("shopping_list", [])
    language = result.get("language", "en")
    
    quality_issues = []
    
    # Check confidence
    confidence_check = check_confidence(confidence)
    if confidence_check["status"] == "rejected":
        quality_issues.append(confidence_check)
    
    # Check if shopping list is empty but confidence is high
    if not shopping_list and confidence > 0.7:
        quality_issues.append({
            "status": "warning",
            "reason": "empty_list_high_confidence",
            "message": "I didn't find any specific items to purchase. Could you tell me exactly what products you need?"
        })
    
    # Check for vague items
    vague_keywords = ["thing", "stuff", "something", "anything", "everything"]
    for item in shopping_list:
        item_name = item.get("item", "").lower()
        if any(keyword in item_name for keyword in vague_keywords):
            quality_issues.append({
                "status": "warning",
                "reason": "vague_item",
                "message": f"The item '{item.get('item')}' is too vague. Could you be more specific about the product?"
            })
            break
    
    # Overall quality score
    quality_score = max(0.0, 1.0 - len(quality_issues) * 0.2)
    
    return {
        "quality_score": quality_score,
        "issues": quality_issues,
        "should_process": not any(issue["status"] == "rejected" for issue in quality_issues),
        "requires_clarification": any(issue["status"] == "warning" for issue in quality_issues)
    }

def generate_refusal_response(quality_issues: List[Dict[str, Any]], language: str = "en") -> Dict[str, str]:
    """
    Generate appropriate refusal responses based on quality issues.
    
    Args:
        quality_issues: List of quality validation issues
        language: Detected language (en, ar, other)
        
    Returns:
        Dictionary with English and Arabic refusal messages
    """
    if not quality_issues:
        return {
            "response_en": "I'm ready to help!",
            "response_ar": "أنا مستعد للمساعدة!"
        }
    
    # Use the first rejection issue as the primary reason
    primary_issue = next((issue for issue in quality_issues if issue["status"] == "rejected"), quality_issues[0])
    message = primary_issue.get("message", "I need more information to help you properly.")
    
    # Generate natural responses
    if language == "ar":
        response_ar = f"{message} هل يمكنك تقديم المزيد من التفاصيل؟"
        response_en = f"{message} Could you provide more details?"
    else:
        response_en = f"{message} Could you provide more details?"
        response_ar = f"{message} هل يمكنك تقديم المزيد من التفاصيل؟"
    
    return {
        "response_en": response_en,
        "response_ar": response_ar
    }

def calculate_metrics(result: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate performance metrics for evaluation.
    
    Args:
        result: Pipeline result
        
    Returns:
        Dictionary of performance metrics
    """
    confidence = result.get("confidence", 0.0)
    grounding_score = result.get("grounding_score", 1.0)
    shopping_list = result.get("shopping_list", [])
    recommended_products = result.get("recommended_products", [])
    
    # Calculate metrics
    extraction_quality = confidence if shopping_list else (1.0 - confidence)
    grounding_quality = grounding_score
    product_match_rate = len(recommended_products) / len(shopping_list) if shopping_list else 1.0
    
    # Overall score
    overall_score = (extraction_quality * 0.4 + grounding_quality * 0.4 + product_match_rate * 0.2)
    
    return {
        "extraction_quality": extraction_quality,
        "grounding_quality": grounding_quality,
        "product_match_rate": product_match_rate,
        "overall_score": overall_score,
        "confidence": confidence,
        "grounding_score": grounding_score
    }
