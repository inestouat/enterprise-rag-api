from typing import List, Dict
from app.retrieval.bm25_index import BM25Index
from app.retrieval.vector_store import VectorStore

class HybridRetriever:
    def __init__(self):
        self.bm25 = BM25Index()
        self.vector = VectorStore()
        self.all_documents = []
    
    def is_ready(self) -> bool:
        return True
    
    def build_bm25_index(self):
        """Load all documents from ChromaDB and build BM25 index"""
        # Get all documents from ChromaDB
        results = self.vector.collection.get(
            include=["documents", "metadatas"]
        )
        
        documents = []
        for i in range(len(results["ids"])):
            documents.append({
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
        
        self.all_documents = documents
        self.bm25.build_index(documents)
        print(f"🔧 Hybrid retriever ready: {len(documents)} documents indexed")
    
    def hybrid_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Combine BM25 + Vector search with RRF fusion"""
        # BM25 search
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        
        # Vector search
        vector_results = self.vector.search(query, top_k=top_k * 2)
        
        # RRF Fusion (Reciprocal Rank Fusion)
        scores = {}
        
        # Score BM25 results
        for rank, (idx, bm25_score) in enumerate(bm25_results):
            doc_id = self.bm25.documents[idx]["id"]
            if doc_id not in scores:
                scores[doc_id] = {"bm25_rank": rank + 1, "vector_rank": None, "doc": self.bm25.documents[idx]}
            else:
                scores[doc_id]["bm25_rank"] = rank + 1
        
        # Score Vector results
        for rank, vec_doc in enumerate(vector_results):
            doc_id = vec_doc["id"]
            if doc_id not in scores:
                scores[doc_id] = {"bm25_rank": None, "vector_rank": rank + 1, "doc": vec_doc}
            else:
                scores[doc_id]["vector_rank"] = rank + 1
        
        # Calculate RRF scores
        k = 60  # RRF constant
        final_scores = []
        
        for doc_id, data in scores.items():
            bm25_rank = data["bm25_rank"] or 999
            vector_rank = data["vector_rank"] or 999
            
            # RRF formula: 1/(k + rank)
            rrf_score = 1/(k + bm25_rank) + 1/(k + vector_rank)
            
            doc = data["doc"]
            final_scores.append({
                "id": doc_id,
                "text": doc["text"] if isinstance(doc, dict) else doc.get("text", ""),
                "metadata": doc.get("metadata", {}) if isinstance(doc, dict) else doc.get("metadata", {}),
                "rrf_score": rrf_score,
                "bm25_rank": bm25_rank if bm25_rank != 999 else None,
                "vector_rank": vector_rank if vector_rank != 999 else None
            })
        
        # Sort by RRF score descending
        final_scores.sort(key=lambda x: x["rrf_score"], reverse=True)
        
        return final_scores[:top_k]