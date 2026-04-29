"""
app/agent.py — Agent Loop for Self-Correction and Refinement

Implements iterative improvement of extraction results through
multiple attempts with refined prompts and strategies.
"""

import json
from typing import Dict, Any, List, Optional

from .extractor import extract_structure
from .utils import validate_extraction_quality, CONFIDENCE_THRESHOLD

class ExtractionAgent:
    """
    Intelligent agent that iteratively refines extraction results
    to achieve higher confidence and accuracy.
    """
    
    def __init__(self, max_retries: int = 3, min_confidence: float = 0.7):
        self.max_retries = max_retries
        self.min_confidence = min_confidence
        self.retry_strategies = [
            "default",
            "detailed", 
            "conservative",
            "focused"
        ]
    
    def refine_extraction(self, text: str, language: str = "en", context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Iteratively refine extraction until confidence threshold is met.
        
        Args:
            text: Input text to extract from
            language: Language hint
            context: Additional context for extraction
            
        Returns:
            Best extraction result from all attempts
        """
        attempts = []
        best_result = None
        best_confidence = 0.0
        
        for attempt in range(self.max_retries):
            strategy = self.retry_strategies[min(attempt, len(self.retry_strategies) - 1)]
            
            try:
                # Extract with current strategy
                result = self._extract_with_strategy(text, language, strategy, context)
                attempts.append({
                    "attempt": attempt + 1,
                    "strategy": strategy,
                    "result": result,
                    "confidence": result.get("confidence", 0.0)
                })
                
                # Track best result
                confidence = result.get("confidence", 0.0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = result
                
                # Early termination if we meet threshold
                if confidence >= self.min_confidence:
                    break
                    
            except Exception as e:
                attempts.append({
                    "attempt": attempt + 1,
                    "strategy": strategy,
                    "error": str(e),
                    "confidence": 0.0
                })
        
        # Add metadata to best result (avoid circular references)
        if best_result:
            # Create clean attempts summary without full results
            attempts_summary = []
            for attempt in attempts:
                summary = {
                    "attempt": attempt["attempt"],
                    "response_ar": "I couldn't extract clear shopping items from your request. Could you be more specific about the products you need?",
                    "confidence": attempt.get("confidence", 0.0)
                }
                if "error" in attempt:
                    summary["error"] = attempt["error"]
                attempts_summary.append(summary)
            
            best_result["agent_metadata"] = {
                "total_attempts": len(attempts_summary),
                "best_attempt": attempts_summary.index(next(a for a in attempts_summary if a["confidence"] == best_confidence)) + 1,
                "attempts": attempts_summary,
                "self_corrected": len(attempts_summary) > 1 and best_confidence > attempts_summary[0].get("confidence", 0.0)
            }
        
        return best_result or self._create_fallback_result(text, language)
    
    def _extract_with_strategy(self, text: str, language: str, strategy: str, context: Optional[Dict]) -> Dict[str, Any]:
        """
        Extract using a specific strategy.
        
        Args:
            text: Input text
            language: Language hint  
            strategy: Extraction strategy
            context: Additional context
            
        Returns:
            Extraction result
        """
        if strategy == "default":
            return extract_structure(text, language)
        
        elif strategy == "detailed":
            # Add context about previous attempts
            enhanced_text = text
            if context and context.get("previous_errors"):
                enhanced_text = f"Previous errors to avoid: {context['previous_errors']}.\\n\\nOriginal text: {text}"
            return extract_structure(enhanced_text, language)
        
        elif strategy == "conservative":
            # Force conservative extraction (lower confidence threshold)
            result = extract_structure(text, language)
            if result.get("confidence", 0.0) > 0.8:
                # If too confident, might be hallucinating - reduce confidence
                result["confidence"] = max(0.6, result["confidence"] - 0.2)
            return result
        
        elif strategy == "focused":
            # Focus only on clear product mentions
            result = extract_structure(text, language)
            
            # Filter out uncertain items
            shopping_list = result.get("shopping_list", [])
            filtered_list = []
            
            for item in shopping_list:
                item_name = item.get("item", "").lower()
                # Keep only clear product names
                if len(item_name) > 2 and not any(word in item_name for word in ["thing", "stuff", "something"]):
                    filtered_list.append(item)
            
            result["shopping_list"] = filtered_list
            
            # Adjust confidence based on filtering
            if len(filtered_list) < len(shopping_list):
                result["confidence"] = max(0.5, result["confidence"] - 0.1)
            
            return result
        
        else:
            return extract_structure(text, language)
    
    def _create_fallback_result(self, text: str, language: str) -> Dict[str, Any]:
        """
        Create a safe fallback result when all attempts fail.
        
        Args:
            text: Original input text
            language: Language hint
            
        Returns:
            Safe fallback result
        """
        return {
            "shopping_list": [],
            "schedule": [],
            "language": language,
            "confidence": 0.1,
            "grounded": False,
            "refusal": "I couldn't extract clear shopping items from your request. Could you be more specific about the products you need?",
            "response_en": "I couldn't extract clear shopping items from your request. Could you be more specific about the products you need?",
            "response_ar": "أنا لم أتمكن من استخراج عناصر الشراء الواضحة من طلبك. هل يمكنك أن تكون أكثر تحديدًا حول المنتجات التي تريدها؟",
            "agent_metadata": {
                "total_attempts": self.max_retries,
                "best_attempt": 0,
                "attempts": [],
                "self_corrected": False,
                "fallback": True
            }
        }

def smart_refine(text: str, language: str = "en", max_retries: int = 3) -> Dict[str, Any]:
    """
    Convenience function for smart extraction refinement.
    
    Args:
        text: Input text
        language: Language hint
        max_retries: Maximum refinement attempts
        
    Returns:
        Refined extraction result
    """
    agent = ExtractionAgent(max_retries=max_retries)
    return agent.refine_extraction(text, language)

def should_retry(result: Dict[str, Any]) -> bool:
    """
    Determine if extraction should be retried based on quality.
    
    Args:
        result: Extraction result
        
    Returns:
        True if retry is recommended
    """
    confidence = result.get("confidence", 0.0)
    shopping_list = result.get("shopping_list", [])
    
    # Retry if confidence is low but not empty
    if confidence < CONFIDENCE_THRESHOLD and shopping_list:
        return True
    
    # Retry if confidence is high but list is empty (possible error)
    if confidence > 0.8 and not shopping_list:
        return True
    
    return False
