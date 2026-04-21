from PyPDF2 import PdfReader
from docx import Document
from typing import List, Tuple
import os

def parse_pdf(file_path: str) -> Tuple[str, List[int]]:
    """Extract text from text-based PDF with page numbers"""
    reader = PdfReader(file_path)
    pages = []
    page_numbers = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(text)
            page_numbers.append(i + 1)
    
    return "\n".join(pages), page_numbers

def parse_docx(file_path: str) -> str:
    """Extract text from Word document"""
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

def parse_txt(file_path: str) -> str:
    """Read text file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_document(file_path: str) -> Tuple[str, List[int], bool]:
    """Route to correct parser based on file type"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        from app.ingestion.ocr import is_scanned_pdf, ocr_pdf
        
        if is_scanned_pdf(file_path):
            text = ocr_pdf(file_path)
            return text, list(range(1, 100)), True  # Estimated pages, OCR used
        else:
            text, pages = parse_pdf(file_path)
            return text, pages, False
    
    elif ext == '.docx':
        return parse_docx(file_path), [1], False
    
    elif ext == '.txt':
        return parse_txt(file_path), [1], False
    
    else:
        raise ValueError(f"Unsupported format: {ext}")