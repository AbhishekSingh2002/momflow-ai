"""
rag/reranker.py — LLM-based Re-ranking System

Uses GPT-4o-mini to re-rank retrieved products for optimal relevance.
This is the final layer of the advanced retrieval system.
"""

import json
import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMReranker:
    """LLM-based product re-ranker for improved relevance."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
    
    def _format_products_for_prompt(self, products: List[Dict[str, Any]]) -> str:
        """Format products for the LLM prompt."""
        product_texts = []
        for i, product in enumerate(products, 1):
            product_text = f"""
{i}. {product['name']}
   - Brand: {product['brand']}
   - Category: {product['category']}
   - Price: ${product['price']}
   - Description: {product.get('description', 'No description')}
   - Match Score: {product.get('combined_score', product.get('similarity_score', 'N/A'))}
"""
            product_texts.append(product_text)
        
        return "\n".join(product_texts)
    
    def rerank(self, query: str, products: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Re-rank products based on query relevance using LLM.
        
        Args:
            query: Original search query
            products: List of retrieved products
            top_k: Number of top results to return
            
        Returns:
            Re-ranked list of products
        """
        if not products:
            return []
        
        if len(products) <= 1:
            return products
        
        # Create the ranking prompt
        products_text = self._format_products_for_prompt(products)
        
        prompt = f"""
You are a product recommendation expert for a baby care shopping assistant.

TASK: Rank the following products based on relevance to the customer's query: "{query}"

CUSTOMER QUERY: "{query}"

AVAILABLE PRODUCTS:
{products_text}

RANKING CRITERIA:
1. Direct relevance to the specific item requested
2. Brand quality and popularity
3. Price appropriateness
4. Product description match
5. Overall suitability for the customer's needs

INSTRUCTIONS:
1. Analyze each product's relevance to the query
2. Consider both exact matches and semantic relevance
3. Rank from MOST relevant (1) to LEAST relevant
4. Return only the top {top_k} products
5. Format your response as a JSON array with product IDs in ranking order

RESPONSE FORMAT:
{{"ranked_ids": ["prod_001", "prod_003", "prod_002"]}}

Please provide the ranking:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise product ranking assistant. Always respond with valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent ranking
                max_tokens=200
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Find JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    ranking_data = json.loads(json_str)
                    ranked_ids = ranking_data.get("ranked_ids", [])
                else:
                    # Fallback: try to parse entire response as JSON
                    ranking_data = json.loads(content)
                    ranked_ids = ranking_data.get("ranked_ids", [])
            except json.JSONDecodeError:
                # If JSON parsing fails, return original order
                print(f"Warning: Could not parse LLM ranking response: {content}")
                return products[:top_k]
            
            # Reorder products based on ranking
            id_to_product = {product["id"]: product for product in products}
            reranked_products = []
            
            for product_id in ranked_ids:
                if product_id in id_to_product:
                    product = id_to_product[product_id].copy()
                    product["rerank_score"] = len(ranked_ids) - ranked_ids.index(product_id)
                    product["ranking_method"] = "llm"
                    reranked_products.append(product)
            
            # Add any missing products that weren't ranked
            for product in products:
                if product["id"] not in ranked_ids and len(reranked_products) < top_k:
                    product_copy = product.copy()
                    product_copy["rerank_score"] = 0
                    product_copy["ranking_method"] = "fallback"
                    reranked_products.append(product_copy)
            
            return reranked_products[:top_k]
            
        except Exception as e:
            print(f"Error in LLM reranking: {e}")
            # Fallback to original order
            return products[:top_k]
    
    def explain_ranking(self, query: str, products: List[Dict[str, Any]]) -> str:
        """
        Get explanation for why products were ranked this way.
        
        Args:
            query: Original search query
            products: List of ranked products
            
        Returns:
            Explanation string
        """
        if not products:
            return "No products to explain."
        
        prompt = f"""
Explain why these products are good recommendations for the query: "{query}"

RANKED PRODUCTS:
{self._format_products_for_prompt(products[:3])}

Provide a brief explanation (2-3 sentences) for why these products were selected:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return "Products selected based on relevance to your search query."

# Global instance for easy access
_reranker = None

def get_reranker() -> LLMReranker:
    """Get or create the global reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = LLMReranker()
    return _reranker

def rerank(query: str, products: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Convenience function to re-rank products.
    
    Args:
        query: Search query
        products: List of products to re-rank
        top_k: Number of top results to return
        
    Returns:
        Re-ranked list of products
    """
    reranker = get_reranker()
    return reranker.rerank(query, products, top_k)
