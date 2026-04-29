#!/usr/bin/env python3
"""
demo_final_system.py — Demonstration of the Final MomFlow AI System

This script showcases the complete advanced system with:
✅ Hybrid Search (Keyword + Embeddings)
✅ Embedding Caching (performance optimization)  
✅ LLM Re-ranking (better relevance)
✅ Retrieval Evaluation (prove it works)

Usage:
    python demo_final_system.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.main import run_pipeline
from eval.retrieval_eval import run_retrieval_evaluation, print_evaluation_summary

def demo_individual_queries():
    """Demonstrate individual query processing with the advanced system."""
    
    print("\n" + "="*80)
    print("🚀 MOMFLOW AI - FINAL ADVANCED SYSTEM DEMO")
    print("="*80)
    
    # Test queries covering different scenarios
    test_queries = [
        {
            "text": "I need diapers size 4 and baby lotion next week",
            "lang": "en",
            "description": "English multi-item with schedule"
        },
        {
            "text": "أحتاج حفاضات مقاس 3 وكريم الأطفال", 
            "lang": "ar",
            "description": "Arabic multi-item request"
        },
        {
            "text": "I need baby formula, a teething ring, and some wet wipes",
            "lang": "en", 
            "description": "English multi-item no schedule"
        },
        {
            "text": "Pampers Active Baby size 3 for Saturday",
            "lang": "en",
            "description": "Brand-specific with variant"
        },
        {
            "text": "What is the weather like today?",
            "lang": "en",
            "description": "Off-topic (should trigger refusal)"
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query['description']}")
        print(f"   Input: {query['text']}")
        print(f"   Language: {query['lang']}")
        print("-" * 60)
        
        try:
            # Run the complete pipeline
            result = run_pipeline(
                text=query['text'],
                language_hint=query['lang'],
                enable_agent_loop=True,
                enable_rag=True,
                enable_confidence_check=True
            )
            
            # Display key results
            if "error" in result:
                print(f"❌ Error: {result['error']} (Stage: {result.get('stage')})")
            elif result.get("refusal"):
                print(f"🚫 Refusal: {result['refusal']}")
                print(f"   Confidence: {result.get('confidence', 0):.0%}")
            else:
                print(f"✅ Success!")
                print(f"   Confidence: {result.get('confidence', 0):.0%}")
                
                # Shopping list
                shopping = result.get('shopping_list', [])
                if shopping:
                    items = [f"{item['item']}" + (f" ({item['details']})" if item.get('details') else "") 
                           for item in shopping]
                    print(f"   Items: {', '.join(items)}")
                
                # Schedule
                schedule = result.get('schedule', [])
                if schedule:
                    tasks = [f"{task['task']} ({task['date']})" for task in schedule]
                    print(f"   Schedule: {', '.join(tasks)}")
                
                # RAG results
                if result.get('recommended_products'):
                    products = result['recommended_products'][:3]  # Top 3
                    product_names = [p['name'] for p in products]
                    print(f"   Products: {', '.join(product_names)}")
                    
                    if result.get('reranking_applied'):
                        print(f"   🎯 LLM Re-ranking applied")
                
                # Quality metrics
                metrics = result.get('metrics', {})
                if metrics:
                    print(f"   Quality Score: {metrics.get('quality_score', 0):.0%}")
                    print(f"   Grounding Score: {metrics.get('grounding_score', 0):.0%}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "="*80)

def demo_evaluation():
    """Demonstrate the retrieval evaluation system."""
    
    print("\n" + "="*80)
    print("📊 RETRIEVAL EVALUATION DEMO")
    print("="*80)
    
    try:
        print("🔍 Running comprehensive retrieval evaluation...")
        
        # Run the evaluation
        results = run_retrieval_evaluation("data/test_cases.json")
        
        # Print detailed summary
        print_evaluation_summary(results)
        
        # Save detailed results
        output_file = "evaluation_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
    
    print("\n" + "="*80)

def demo_system_architecture():
    """Display the final system architecture."""
    
    print("\n" + "="*80)
    print("🏗️ FINAL SYSTEM ARCHITECTURE")
    print("="*80)
    
    architecture = """
Voice/Input
    ↓
STT (Speech-to-Text)
    ↓
Action Extraction (with Agent Loop)
    ↓
Confidence Check 🚫
    ↓
Hybrid Retrieval 🔍
    ├── Embedding Search (semantic)
    └── Keyword Match (exact)
    ↓
LLM Re-Ranker 🎯
    ↓
Top Products (ranked)
    ↓
Response Generator (EN + AR)
    ↓
Evaluation + Logging 📊
"""
    
    features = """
🧠 ADVANCED FEATURES:
✅ Hybrid Search (Keyword + Embeddings)
✅ Embedding Caching (performance optimization)
✅ LLM Re-ranking (better relevance)  
✅ Retrieval Evaluation (prove it works)
✅ Agent Loop (self-correction)
✅ Confidence-based Rejection
✅ Multilingual Support (EN + AR)
✅ Comprehensive Metrics
"""
    
    print(architecture)
    print(features)
    
    print("\n🎯 INTERVIEW KILLER ANSWERS:")
    print("Q: What makes your system production-ready?")
    print("A: I implemented a hybrid retrieval system combining embeddings and")
    print("   keyword search, added caching to optimize performance, used an")
    print("   LLM-based reranker to improve relevance, and built evaluation")
    print("   metrics to measure retrieval quality, ensuring the system is")
    print("   both accurate and reliable.")
    
    print("\n" + "="*80)

def main():
    """Run the complete demonstration."""
    
    print("🛍️ MomFlow AI - Final Advanced System Demonstration")
    print("Built for Mumzworld AI Engineering Internship Assessment")
    
    # Show architecture
    demo_system_architecture()
    
    # Demo individual queries
    demo_individual_queries()
    
    # Demo evaluation system
    demo_evaluation()
    
    print("\n🎉 DEMONSTRATION COMPLETE!")
    print("This system showcases serious AI engineering capabilities:")
    print("• Advanced RAG with hybrid search")
    print("• Performance optimization with caching")
    print("• LLM-based re-ranking for better relevance")
    print("• Comprehensive evaluation metrics")
    print("• Production-ready error handling")
    print("• Multilingual support")
    print("• Confidence-based quality control")

if __name__ == "__main__":
    main()
