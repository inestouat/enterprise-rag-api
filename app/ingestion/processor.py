from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer
import os

from app.core.config import settings
from app.ingestion.parser import parse_document
from app.ingestion.chunker import chunk_document

class DocumentProcessor:
    def __init__(self):
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Initialize ChromaDB (new API)
        os.makedirs("data/chroma", exist_ok=True)
        self.client = chromadb.PersistentClient(path="data/chroma")
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="enterprise_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.documents_db = {}  # Simple in-memory tracking
    
    def is_ready(self) -> bool:
        return True
    
    async def process(self, file_path: str, doc_id: str, filename: str) -> Dict:
        """Full pipeline: parse → chunk → embed → store"""
        print(f" Processing: {filename}")
        
        # Step 1: Parse (with OCR if needed)
        text, pages, ocr_used = parse_document(file_path)
        print(f" Extracted {len(text)} characters (OCR: {ocr_used})")
        
        # Step 2: Chunk
        chunks = chunk_document(text, filename, pages, ocr_used)
        
        # Step 3: Embed
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=True)
        
        # Step 4: Store in ChromaDB
        self.collection.add(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks],
            embeddings=embeddings.tolist()
        )
        
        # Track document
        self.documents_db[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "chunks": len(chunks),
            "ocr_used": ocr_used,
            "char_count": len(text)
        }
        
        print(f" Indexed {len(chunks)} chunks")
        return {
            "chunks": len(chunks),
            "ocr_used": ocr_used,
            "char_count": len(text)
        }
    
    async def list_documents(self) -> List[Dict]:
        """Return all indexed documents"""
        return list(self.documents_db.values())