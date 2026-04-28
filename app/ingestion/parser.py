from PyPDF2 import PdfReader
from docx import Document
from typing import List, Tuple
import os

def parse_pdf(file_path: str) -> Tuple[str, List[int]]:
    """Extract text from PDF"""
    reader = PdfReader(file_path)
    pages = []
    page_numbers = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append(text)
            page_numbers.append(i + 1)
    return "\n".join(pages), page_numbers

def parse_docx(file_path: str) -> str:
    """Extract text from Word document"""
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

def parse_txt(file_path: str) -> str:
    """Read plain text file"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def parse_document(file_path: str) -> Tuple[str, List[int]]:
    """Route to correct parser based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        text, pages = parse_pdf(file_path)
        return text, pages
    elif ext == '.docx':
        return parse_docx(file_path), [1]
    elif ext == '.txt':
        return parse_txt(file_path), [1]
    else:
        raise ValueError(f"Unsupported format: {ext}")