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
        os.makedirs("data/chroma", exist_ok=True)
        self.client = chromadb.PersistentClient(path="data/chroma")
        self.collection = self.client.get_or_create_collection(
            name="enterprise_documents",
            metadata={"hnsw:space": "cosine"}
        )
        self.documents_db = {}

    async def process(self, file_path: str, doc_id: str, filename: str, hybrid_retriever=None) -> Dict:
        print(f"📥 Processing: {filename}")

        # 1. Parse
        text, pages = parse_document(file_path)

        # 2. Chunk
        chunks = chunk_document(text, filename, pages)

        # 3. Embed & store in ChromaDB
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=True)

        self.collection.add(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks],
            embeddings=embeddings.tolist()
        )

        # 4. Rebuild BM25 index after adding new documents
        if hybrid_retriever:
            print("🔄 Rebuilding BM25 index...")
            hybrid_retriever.build_bm25_index()

        self.documents_db[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "chunks": len(chunks),
            "char_count": len(text)
        }

        print(f"✅ Indexed {len(chunks)} chunks from {filename}")
        return {"chunks": len(chunks), "char_count": len(text)}

    def is_ready(self) -> bool:
        return True

    def list_documents(self) -> List[Dict]:
        return list(self.documents_db.values())