"""
rag/retriever.py — Hybrid Product Retrieval and Grounding System

Implements advanced RAG combining semantic embeddings and keyword search
for optimal retrieval performance and accuracy.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from difflib import SequenceMatcher
from .vector_store import VectorStore

def load_products() -> List[Dict[str, Any]]:
    """Load product database from JSON file."""
    try:
        products_path = Path(__file__).parent / "products.json"
        with open(products_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("Product database not found. Run setup first.")
    except json.JSONDecodeError:
        raise ValueError("Invalid product database format.")

def similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def keyword_match(query: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Perform exact keyword matching on products.
    
    Args:
        query: Search query string
        products: List of products to search
        
    Returns:
        List of matching products with keyword scores
    """
    results = []
    query_lower = query.lower()
    
    for product in products:
        # Check for exact keyword matches
        name_match = query_lower in product["name"].lower()
        category_match = query_lower in product["category"].lower()
        brand_match = query_lower in product["brand"].lower()
        desc_match = query_lower in product.get("description", "").lower()
        
        if name_match or category_match or brand_match or desc_match:
            # Calculate keyword score based on match type
            score = 1.0 if name_match else 0.8 if category_match else 0.6 if brand_match else 0.4
            
            results.append({
                **product,
                "keyword_score": score,
                "match_type": "keyword"
            })
    
    return results

def retrieve_products(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval combining semantic search and keyword matching.
    
    Args:
        actions: List of extracted actions with items
        
    Returns:
        List of relevant products from hybrid search
    """
    if not actions:
        return []
    
    # Initialize vector store
    store = VectorStore()
    store.load_data()
    all_products = store.products
    final_results = []
    
    for action in actions:
        item = action.get("item", "").strip()
        if not item:
            continue
        
        # Semantic search using embeddings
        semantic_results = store.search(item, top_k=3)
        
        # Keyword matching
        keyword_results = keyword_match(item, all_products)
        
        # Merge and deduplicate results
        combined = {}
        
        # Add semantic results
        for product in semantic_results:
            product_key = product["id"]
            combined[product_key] = {
                **product,
                "search_sources": ["semantic"]
            }
        
        # Add keyword results and merge
        for product in keyword_results:
            product_key = product["id"]
            if product_key in combined:
                # Merge scores if product already exists
                combined[product_key]["keyword_score"] = product["keyword_score"]
                if "keyword" not in combined[product_key]["search_sources"]:
                    combined[product_key]["search_sources"].append("keyword")
            else:
                combined[product_key] = {
                    **product,
                    "search_sources": ["keyword"]
                }
        
        # Convert to list and sort by combined relevance
        merged_results = list(combined.values())
        
        # Calculate combined score
        for product in merged_results:
            semantic_score = product.get("similarity_score", 0)
            keyword_score = product.get("keyword_score", 0)
            
            # Weighted combination (semantic gets higher weight)
            product["combined_score"] = (semantic_score * 0.7) + (keyword_score * 0.3)
        
        # Sort and take top results for this item
        merged_results.sort(key=lambda x: x["combined_score"], reverse=True)
        final_results.extend(merged_results[:3])  # Top 3 per item
    
    # Remove duplicates across different items and sort globally
    seen_ids = set()
    unique_results = []
    for product in final_results:
        if product["id"] not in seen_ids:
            seen_ids.add(product["id"])
            unique_results.append(product)
    
    # Final global sort
    unique_results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
    return unique_results[:5]  # Return top 5 overall

def ground_shopping_list(shopping_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ground shopping list using hybrid retrieval system.
    
    Returns:
        Dictionary with grounded items and recommendations
    """
    if not shopping_list:
        return {
            "grounded_items": [],
            "recommended_products": [],
            "unmatched_items": [],
            "grounding_score": 1.0,
            "retrieval_method": "hybrid"
        }
    
    # Use hybrid retrieval
    recommended_products = retrieve_products(shopping_list)
    
    # Track which items were matched (using hybrid approach)
    matched_items = set()
    for product in recommended_products:
        # Check if this product matches any shopping list item
        for item in shopping_list:
            item_name = item.get("item", "").lower()
            if (item_name in product["name"].lower() or 
                item_name in product["category"].lower() or
                item_name in product["brand"].lower()):
                matched_items.add(item_name)
                break
    
    # Categorize items
    grounded_items = [item for item in shopping_list if item.get("item", "").lower() in matched_items]
    unmatched_items = [item for item in shopping_list if item.get("item", "").lower() not in matched_items]
    
    # Calculate grounding score
    grounding_score = len(grounded_items) / len(shopping_list) if shopping_list else 1.0
    
    return {
        "grounded_items": grounded_items,
        "recommended_products": recommended_products,
        "unmatched_items": unmatched_items,
        "grounding_score": grounding_score,
        "retrieval_method": "hybrid",
        "total_searched": len(shopping_list),
        "total_found": len(recommended_products)
    }

def search_products(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search products by query string.
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of matching products
    """
    products = load_products()
    results = []
    
    query_lower = query.lower()
    
    for product in products:
        # Search in name, category, brand, and description
        searchable_text = f"{product['name']} {product['category']} {product['brand']} {product.get('description', '')}"
        score = similarity_score(query_lower, searchable_text)
        
        if score > 0.3:  # Lower threshold for general search
            results.append({
                **product,
                "match_score": score
            })
    
    # Sort and limit results
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:limit]
