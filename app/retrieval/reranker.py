from typing import List, Dict
from sentence_transformers import CrossEncoder
import numpy as np
from app.core.config import settings

class Reranker:
    def __init__(self):
        print("⏳ Loading cross-encoder model...")
        self.model = CrossEncoder(settings.RERANKER_MODEL)
        print("✅ Cross-encoder ready")
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """Rerank documents by relevance to query"""
        if not documents:
            return []
        
        # Prepare pairs: (query, document_text)
        pairs = [(query, doc["text"]) for doc in documents]
        
        # Get scores
        scores = self.model.predict(pairs)
        
        # Normalize scores to 0-1 range (sigmoid)
        normalized_scores = 1 / (1 + np.exp(-scores))
        
        # Add scores to documents
        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(normalized_scores[i])
        
        # Sort by rerank score descending
        documents.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        return documents[:top_k]