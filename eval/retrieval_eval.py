"""
eval/retrieval_eval.py — Retrieval Evaluation System

Comprehensive evaluation metrics for the hybrid retrieval system including
precision, recall, and relevance scoring.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import statistics

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from rag.retriever import retrieve_products
from rag.reranker import rerank

def evaluate_retrieval(predicted_products: List[Dict[str, Any]], expected_items: List[str]) -> Dict[str, float]:
    """
    Evaluate retrieval quality against expected items.
    
    Args:
        predicted_products: List of retrieved products
        expected_items: List of expected product names/brands
        
    Returns:
        Dictionary with evaluation metrics
    """
    if not expected_items:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "hit_rate": 0.0,
            "mrr": 0.0
        }
    
    # Convert expected items to lowercase for matching
    expected_lower = [item.lower() for item in expected_items]
    
    hits = 0
    hit_positions = []
    
    for i, product in enumerate(predicted_products):
        product_name = product.get("name", "").lower()
        product_brand = product.get("brand", "").lower()
        product_category = product.get("category", "").lower()
        
        # Check if product matches any expected item
        for expected_item in expected_lower:
            if (expected_item in product_name or 
                expected_item in product_brand or 
                expected_item in product_category):
                hits += 1
                hit_positions.append(i + 1)  # 1-indexed position
                break
    
    # Calculate metrics
    precision = hits / len(predicted_products) if predicted_products else 0.0
    recall = hits / len(expected_items) if expected_items else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    hit_rate = 1.0 if hits > 0 else 0.0
    
    # Mean Reciprocal Rank (MRR) - position of first relevant result
    mrr = 1.0 / hit_positions[0] if hit_positions else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "hit_rate": hit_rate,
        "mrr": mrr,
        "hits": hits,
        "total_expected": len(expected_items),
        "total_predicted": len(predicted_products)
    }

def evaluate_reranking(original_products: List[Dict[str, Any]], 
                      reranked_products: List[Dict[str, Any]], 
                      expected_items: List[str]) -> Dict[str, float]:
    """
    Evaluate the impact of LLM re-ranking.
    
    Args:
        original_products: Products before re-ranking
        reranked_products: Products after re-ranking
        expected_items: Expected product names/brands
        
    Returns:
        Dictionary comparing before/after metrics
    """
    original_metrics = evaluate_retrieval(original_products, expected_items)
    reranked_metrics = evaluate_retrieval(reranked_products, expected_items)
    
    # Calculate improvements
    improvements = {}
    for metric in ["precision", "recall", "f1", "hit_rate", "mrr"]:
        improvements[f"{metric}_improvement"] = reranked_metrics[metric] - original_metrics[metric]
    
    return {
        "original": original_metrics,
        "reranked": reranked_metrics,
        "improvements": improvements
    }

def run_retrieval_evaluation(test_cases_path: str = "data/test_cases.json") -> Dict[str, Any]:
    """
    Run comprehensive retrieval evaluation on test cases.
    
    Args:
        test_cases_path: Path to test cases JSON file
        
    Returns:
        Complete evaluation results
    """
    # Load test cases
    try:
        with open(test_cases_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Test cases file not found: {test_cases_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in test cases file: {test_cases_path}")
    
    results = {
        "total_cases": len(test_cases),
        "evaluated_cases": 0,
        "case_results": [],
        "aggregate_metrics": {
            "precision": [],
            "recall": [],
            "f1": [],
            "hit_rate": [],
            "mrr": []
        },
        "reranking_impact": {
            "precision_improvements": [],
            "recall_improvements": [],
            "f1_improvements": [],
            "hit_rate_improvements": [],
            "mrr_improvements": []
        }
    }
    
    for case in test_cases:
        case_id = case.get("id", "unknown")
        
        # Skip cases that should result in refusal
        if case.get("expect_refusal", False):
            continue
        
        # Get expected products (new field for evaluation)
        expected_products = case.get("expected_products", [])
        if not expected_products:
            # Fallback to expected_items
            expected_products = case.get("expected_items", [])
        
        if not expected_products:
            continue
        
        # Extract actions from input (simulate extraction)
        input_text = case.get("input", "")
        
        # Create mock actions based on input
        mock_actions = []
        if "diaper" in input_text.lower():
            mock_actions.append({"item": "diapers"})
        if "lotion" in input_text.lower():
            mock_actions.append({"item": "lotion"})
        if "formula" in input_text.lower() or "milk" in input_text.lower():
            mock_actions.append({"item": "formula"})
        if "wipes" in input_text.lower():
            mock_actions.append({"item": "wipes"})
        if "monitor" in input_text.lower():
            mock_actions.append({"item": "monitor"})
        if "thermometer" in input_text.lower():
            mock_actions.append({"item": "thermometer"})
        
        if not mock_actions:
            continue
        
        try:
            # Test hybrid retrieval
            retrieved_products = retrieve_products(mock_actions)
            
            # Test re-ranking
            query = mock_actions[0].get("item", "")
            reranked_products = rerank(query, retrieved_products, top_k=3)
            
            # Evaluate retrieval
            retrieval_metrics = evaluate_retrieval(retrieved_products, expected_products)
            
            # Evaluate re-ranking impact
            reranking_metrics = evaluate_reranking(retrieved_products, reranked_products, expected_products)
            
            # Store case results
            case_result = {
                "case_id": case_id,
                "input": input_text,
                "expected_products": expected_products,
                "retrieved_count": len(retrieved_products),
                "reranked_count": len(reranked_products),
                "retrieval_metrics": retrieval_metrics,
                "reranking_metrics": reranking_metrics
            }
            
            results["case_results"].append(case_result)
            results["evaluated_cases"] += 1
            
            # Collect aggregate metrics
            for metric in ["precision", "recall", "f1", "hit_rate", "mrr"]:
                results["aggregate_metrics"][metric].append(retrieval_metrics[metric])
            
            # Collect re-ranking improvements
            improvements = reranking_metrics["improvements"]
            for metric in ["precision", "recall", "f1", "hit_rate", "mrr"]:
                results["reranking_impact"][f"{metric}_improvements"].append(
                    improvements[f"{metric}_improvement"]
                )
            
        except Exception as e:
            print(f"Error evaluating case {case_id}: {e}")
            continue
    
    # Calculate aggregate statistics
    for metric in ["precision", "recall", "f1", "hit_rate", "mrr"]:
        values = results["aggregate_metrics"][metric]
        if values:
            results["aggregate_metrics"][f"avg_{metric}"] = statistics.mean(values)
            results["aggregate_metrics"][f"median_{metric}"] = statistics.median(values)
            results["aggregate_metrics"][f"min_{metric}"] = min(values)
            results["aggregate_metrics"][f"max_{metric}"] = max(values)
    
    # Calculate re-ranking impact statistics
    for metric in ["precision", "recall", "f1", "hit_rate", "mrr"]:
        improvements = results["reranking_impact"][f"{metric}_improvements"]
        if improvements:
            results["reranking_impact"][f"avg_{metric}_improvement"] = statistics.mean(improvements)
            results["reranking_impact"][f"median_{metric}_improvement"] = statistics.median(improvements)
    
    return results

def print_evaluation_summary(results: Dict[str, Any]) -> None:
    """Print a formatted summary of evaluation results."""
    print("\n" + "="*60)
    print("MOMFLOW AI - RETRIEVAL EVALUATION SUMMARY")
    print("="*60)
    
    print(f"\nTotal Cases: {results['total_cases']}")
    print(f"Evaluated Cases: {results['evaluated_cases']}")
    
    agg = results["aggregate_metrics"]
    print(f"\n📊 RETRIEVAL PERFORMANCE:")
    print(f"  Precision:  {agg.get('avg_precision', 0):.3f} (median: {agg.get('median_precision', 0):.3f})")
    print(f"  Recall:     {agg.get('avg_recall', 0):.3f} (median: {agg.get('median_recall', 0):.3f})")
    print(f"  F1 Score:   {agg.get('avg_f1', 0):.3f} (median: {agg.get('median_f1', 0):.3f})")
    print(f"  Hit Rate:   {agg.get('avg_hit_rate', 0):.3f} (median: {agg.get('median_hit_rate', 0):.3f})")
    print(f"  MRR:        {agg.get('avg_mrr', 0):.3f} (median: {agg.get('median_mrr', 0):.3f})")
    
    rerank = results["reranking_impact"]
    print(f"\n🎯 RE-RANKING IMPACT:")
    print(f"  Precision Improvement:  {rerank.get('avg_precision_improvement', 0):+.3f}")
    print(f"  Recall Improvement:     {rerank.get('avg_recall_improvement', 0):+.3f}")
    print(f"  F1 Improvement:         {rerank.get('avg_f1_improvement', 0):+.3f}")
    print(f"  Hit Rate Improvement:   {rerank.get('avg_hit_rate_improvement', 0):+.3f}")
    print(f"  MRR Improvement:        {rerank.get('avg_mrr_improvement', 0):+.3f}")
    
    print(f"\n📈 PERFORMANCE ANALYSIS:")
    if agg.get('avg_precision', 0) > 0.7:
        print("  ✅ High precision - system is accurate")
    elif agg.get('avg_precision', 0) > 0.5:
        print("  ⚠️  Moderate precision - room for improvement")
    else:
        print("  ❌ Low precision - needs significant improvement")
    
    if rerank.get('avg_f1_improvement', 0) > 0:
        print("  ✅ Re-ranking is improving results")
    else:
        print("  ⚠️  Re-ranking shows limited impact")
    
    print("\n" + "="*60)

def main():
    """Run retrieval evaluation and print results."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate MomFlow AI retrieval system")
    parser.add_argument("--test-cases", default="data/test_cases.json", 
                       help="Path to test cases JSON file")
    parser.add_argument("--output", help="Output file for detailed results")
    parser.add_argument("--summary-only", action="store_true",
                       help="Only print summary, not detailed results")
    
    args = parser.parse_args()
    
    try:
        print("🚀 Starting retrieval evaluation...")
        results = run_retrieval_evaluation(args.test_cases)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📄 Detailed results saved to: {args.output}")
        
        if not args.summary_only:
            print("\n📋 DETAILED RESULTS:")
            print(json.dumps(results, indent=2, ensure_ascii=False))
        
        print_evaluation_summary(results)
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
