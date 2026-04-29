"""
rag/vector_store.py — Embedding-based Vector Store with Caching

Implements semantic search using embeddings with performance optimization
through caching. This is the foundation of the hybrid retrieval system.
"""

import json
import pickle
import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

CACHE_FILE = "rag/cache.pkl"

class VectorStore:
    """Vector store for semantic product search with caching."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vectors = []
        self.products = []
        self.embeddings_model = "text-embedding-3-small"
        self.is_loaded = False
        
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.embeddings_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to get embedding: {e}")
    
    def _create_product_text(self, product: Dict[str, Any]) -> str:
        """Create searchable text from product."""
        return f"{product.get('name', '')} {product.get('category', '')} {product.get('brand', '')} {product.get('description', '')}"
    
    def load_data(self, path: str = None) -> None:
        """Load product data and compute embeddings with caching."""
        if path is None:
            path = Path(__file__).parent / "products.json"
        
        # Try to load from cache first
        cached = self._load_cache()
        if cached:
            self.vectors, self.products = cached
            print(f"Loaded {len(self.products)} products from cache")
            self.is_loaded = True
            return
        
        # Load products from JSON
        try:
            products_path = Path(path) if isinstance(path, str) else path
            with open(products_path, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Product database not found at {path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid product database format in {path}")
        
        # Compute embeddings for all products
        print(f"Computing embeddings for {len(self.products)} products...")
        self.vectors = []
        
        for product in self.products:
            product_text = self._create_product_text(product)
            embedding = self._get_embedding(product_text)
            self.vectors.append(embedding)
        
        # Save to cache
        self._save_cache(self.vectors, self.products)
        print(f"Computed and cached embeddings for {len(self.products)} products")
        self.is_loaded = True
    
    def _save_cache(self, vectors: List[List[float]], products: List[Dict[str, Any]]) -> None:
        """Save vectors and products to cache file."""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "wb") as f:
                pickle.dump((vectors, products), f)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
    
    def _load_cache(self) -> Optional[Tuple[List[List[float]], List[Dict[str, Any]]]]:
        """Load vectors and products from cache file."""
        if not os.path.exists(CACHE_FILE):
            return None
        
        try:
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products using semantic similarity.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of products with similarity scores
        """
        if not self.vectors or not self.products:
            raise RuntimeError("No data loaded. Call load_data() first.")
        
        # Get embedding for query
        query_embedding = self._get_embedding(query)
        
        # Calculate similarities
        results = []
        for i, product in enumerate(self.products):
            similarity = self._cosine_similarity(query_embedding, self.vectors[i])
            
            if similarity > 0.3:  # Minimum similarity threshold
                results.append({
                    **product,
                    "similarity_score": similarity,
                    "search_type": "semantic"
                })
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            print("Cache cleared")
        else:
            print("No cache file found")

# Global instance for easy access
_store = None

def get_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global _store
    if _store is None:
        _store = VectorStore()
        _store.load_data()
    return _store

def save_cache(vectors: List[List[float]], products: List[Dict[str, Any]]) -> None:
    """Save vectors and products to cache (utility function)."""
    store = VectorStore()
    store._save_cache(vectors, products)

def load_cache() -> Optional[Tuple[List[List[float]], List[Dict[str, Any]]]]:
    """Load vectors and products from cache (utility function)."""
    store = VectorStore()
    return store._load_cache()
