from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict
from app.core.config import settings

def chunk_document(text: str, source: str, pages: List[int]) -> List[Dict]:
    """Split document into chunks with metadata"""
    # Separators ordered by priority: 
    # 1. Double Newline (Paragraphs)
    # 2. Single Newline (List items/Tables)
    # 3. Period (Sentences)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Explicitly using the optimized size
        chunk_overlap=150, 
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )
    
    chunks = splitter.split_text(text)
    chunk_objects = []
    
    for i, chunk in enumerate(chunks):
        # Improved page estimation logic
        page_estimate = pages[min(i, len(pages)-1)] if pages else 1
        
        chunk_objects.append({
            "id": f"{source}_chunk_{i}",
            "text": chunk,
            "metadata": {
                "source": source,
                "page": page_estimate,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "char_count": len(chunk)
            }
        })
    print(f" Created {len(chunks)} chunks from {source}")
    return chunk_objects