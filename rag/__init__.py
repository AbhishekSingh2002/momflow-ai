"""
rag/__init__.py — Retrieval-Augmented Generation Module

Provides product grounding and search capabilities for MomFlow AI.
"""

from .retriever import load_products, retrieve_products, ground_shopping_list, search_products

__all__ = [
    "load_products",
    "retrieve_products", 
    "ground_shopping_list",
    "search_products"
]
