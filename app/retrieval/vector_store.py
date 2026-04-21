from typing import List, Dict, Tuple
import chromadb
from sentence_transformers import SentenceTransformer

from app.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="data/chroma")
        self.collection = self.client.get_or_create_collection(
            name="enterprise_documents"
        )
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Semantic search using vector similarity"""
        # Embed query
        query_embedding = self.embedder.encode([query])[0].tolist()
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "score": 1 - results["distances"][0][i]  # Convert distance to similarity
            })
        
        return formatted