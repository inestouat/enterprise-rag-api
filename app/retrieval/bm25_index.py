from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import re

class BM25Index:
    def __init__(self):
        self.bm25 = None
        self.documents = []
        self.tokenized_corpus = []
    
    def build_index(self, documents: List[Dict]):
        """Build BM25 index from documents"""
        self.documents = documents
        
        # Tokenize: lowercase, remove punctuation, split
        self.tokenized_corpus = []
        for doc in documents:
            text = doc["text"].lower()
            tokens = re.findall(r'\b\w+\b', text)
            self.tokenized_corpus.append(tokens)
        
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"📚 BM25 index built: {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search BM25 index, return (doc_index, score)"""
        if not self.bm25:
            return []
        
        # Tokenize query same way
        query_tokens = re.findall(r'\b\w+\b', query.lower())
        
        # Get scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        
        return [(i, scores[i]) for i in top_indices]
    
    def get_document(self, index: int) -> Dict:
        """Get document by index"""
        if 0 <= index < len(self.documents):
            return self.documents[index]
        return None