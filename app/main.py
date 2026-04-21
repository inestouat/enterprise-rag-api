from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import time

from app.ingestion.processor import DocumentProcessor

app = FastAPI(
    title="Enterprise Document Intelligence API",
    description="Production RAG with hybrid retrieval, reranking, citations, and OCR",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
processor = DocumentProcessor()

class QueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    top_k: int = 5

class Citation(BaseModel):
    source: str
    page: Optional[int] = None
    text: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": ["OCR", "Hybrid Retrieval", "Reranking", "Citations"],
        "components": {
            "ingestion": processor.is_ready(),
            "retrieval": "ready",
            "generation": "ready"
        }
    }

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document (PDF, DOCX, TXT, or scanned images)"""
    try:
        allowed = {'.pdf', '.txt', '.docx', '.png', '.jpg', '.jpeg'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            raise HTTPException(400, f"Unsupported format: {ext}")
        
        doc_id = str(uuid.uuid4())
        temp_path = f"data/temp_{doc_id}{ext}"
        os.makedirs("data", exist_ok=True)
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process and index
        result = await processor.process(temp_path, doc_id, file.filename)
        
        os.remove(temp_path)
        
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "chunks_indexed": result["chunks"],
            "ocr_used": result["ocr_used"],
            "char_count": result["char_count"],
            "status": "indexed"
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Ask a question about your documents"""
    start_total = time.time()
    
    try:
        # TODO: Implement retrieval (Day 3)
        # TODO: Implement generation (Day 4)
        
        return QueryResponse(
            answer="Placeholder answer - full pipeline coming in Days 3-4",
            citations=[],
            retrieval_time_ms=0,
            generation_time_ms=0,
            total_time_ms=round((time.time() - start_total) * 1000, 2)
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/documents")
async def list_documents():
    """List all indexed documents"""
    return await processor.list_documents()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)