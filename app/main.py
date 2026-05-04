from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
import time

from app.ingestion.processor import DocumentProcessor
from app.retrieval.hybrid import HybridRetriever
from app.generation.engine import GenerationEngine
from app.retrieval.confidence import compute_confidence, build_idk_response

app = FastAPI(
    title="DocIQ — Enterprise RAG API",
    description="Production RAG with hybrid retrieval, reranking, confidence scoring, and citations",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = DocumentProcessor()
retriever = HybridRetriever()
generator = GenerationEngine()


# ── Pydantic models ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    top_k: int = 5
    retrieval_mode: str = "hybrid"  # "hybrid" | "dense"

class Citation(BaseModel):
    source: str
    page: Optional[int] = None
    text: str
    score: float

class ConfidenceBreakdown(BaseModel):
    score: float
    tier: str          # "high" | "medium" | "low" | "none"
    can_answer: bool
    reason: str
    top_result_score: float
    avg_score: float
    consistency: float

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: ConfidenceBreakdown
    retrieval_mode: str
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": ["Hybrid Retrieval", "Reranking", "Confidence Scoring", "Citations"],
        "components": {
            "ingestion": processor.is_ready(),
            "retrieval": retriever.is_ready(),
            "generation": generator.is_ready()
        }
    }


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document (PDF, DOCX, TXT)"""
    try:
        allowed = {'.pdf', '.txt', '.docx'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            raise HTTPException(400, f"Unsupported format: {ext}. Allowed: PDF, DOCX, TXT")

        doc_id = str(uuid.uuid4())
        temp_path = f"data/temp_{doc_id}{ext}"
        os.makedirs("data", exist_ok=True)

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        result = await processor.process(temp_path, doc_id, file.filename)
        os.remove(temp_path)
        retriever.build_bm25_index()

        return {
            "document_id": doc_id,
            "filename": file.filename,
            "chunks_indexed": result["chunks"],
            "char_count": result["char_count"],
            "status": "indexed"
        }

    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query your documents with confidence scoring"""
    start_total = time.time()

    try:
        if not retriever.all_documents:
            retriever.build_bm25_index()

        if not retriever.all_documents:
            return QueryResponse(
                answer="No documents indexed yet. Please upload a document first.",
                citations=[],
                confidence=ConfidenceBreakdown(
                    score=0.0, tier="none", can_answer=False,
                    reason="No documents indexed",
                    top_result_score=0.0, avg_score=0.0, consistency=0.0
                ),
                retrieval_mode=request.retrieval_mode,
                retrieval_time_ms=0, generation_time_ms=0, total_time_ms=0
            )

        # Retrieve
        start_retrieval = time.time()
        if request.retrieval_mode == "dense":
            from app.retrieval.vector_store import VectorStore
            vs = VectorStore()
            raw_results = vs.search(request.query, top_k=request.top_k)
            results = retriever.reranker.rerank(request.query, raw_results, top_k=request.top_k)
        else:
            results = retriever.hybrid_search(request.query, top_k=request.top_k)
        retrieval_time = (time.time() - start_retrieval) * 1000

        # Confidence scoring
        confidence = compute_confidence(results)

        # Format citations
        citations = []
        context_parts = []
        for i, result in enumerate(results[:5]):
            citations.append(Citation(
                source=result["metadata"].get("source", "Unknown"),
                page=result["metadata"].get("page", 1),
                text=result["text"][:200] + "...",
                score=round(result.get("rerank_score", result.get("rrf_score", 0)), 4)
            ))
            context_parts.append(f"[{i+1}] {result['text'][:800]}")

        # Generate — or return IDK response if confidence too low
        start_generation = time.time()

        if confidence["can_answer"]:
            context = "\n\n".join(context_parts)
            answer = generator.generate(request.query, context, citations)
        else:
            answer = build_idk_response(request.query, results, confidence)

        generation_time = (time.time() - start_generation) * 1000
        total_time = (time.time() - start_total) * 1000

        return QueryResponse(
            answer=answer,
            citations=citations,
            confidence=ConfidenceBreakdown(**confidence),
            retrieval_mode=request.retrieval_mode,
            retrieval_time_ms=round(retrieval_time, 2),
            generation_time_ms=round(generation_time, 2),
            total_time_ms=round(total_time, 2)
        )

    except Exception as e:
        import traceback
        print(f"\n QUERY ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Query failed: {str(e)}")

@app.get("/documents")
async def list_documents():
    try:
        docs = processor.list_documents()
        # Handle both sync and async versions
        if hasattr(docs, '__await__'):
            docs = await docs
        return docs if isinstance(docs, list) else []
    except Exception as e:
        print(f" /documents error: {e}")
        return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)