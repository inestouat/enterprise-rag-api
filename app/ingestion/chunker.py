from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict
from app.core.config import settings

def chunk_document(text: str, source: str, pages: List[int], ocr_used: bool) -> List[Dict]:
    """Split document into chunks with metadata"""
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )
    
    chunks = splitter.split_text(text)
    
    # Create chunk objects with metadata
    chunk_objects = []
    for i, chunk in enumerate(chunks):
        # Estimate page (rough approximation)
        page_estimate = pages[min(i, len(pages)-1)] if pages else 1
        
        chunk_objects.append({
            "id": f"{source}_chunk_{i}",
            "text": chunk,
            "metadata": {
                "source": source,
                "page": page_estimate,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "ocr_used": ocr_used,
                "char_count": len(chunk)
            }
        })
    
    print(f" Created {len(chunks)} chunks from {source}")
    return chunk_objects