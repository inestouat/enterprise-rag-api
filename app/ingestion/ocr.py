import pytesseract
from PIL import Image
import pdf2image
from typing import List
from app.core.config import settings

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def is_scanned_pdf(file_path: str) -> bool:
    """Detect if PDF is scanned images or text-based"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        
        # Check first few pages for text
        for page in reader.pages[:3]:
            text = page.extract_text()
            if text and len(text.strip()) > 50:
                return False  # Has extractable text
        
        return True  # No text found, likely scanned
    except:
        return True  # Default to OCR if unsure

def ocr_pdf(file_path: str) -> str:
    """Extract text from scanned PDF using OCR"""
    print(f" OCR processing: {file_path}")
    
    # Convert PDF to images
    images = pdf2image.convert_from_path(file_path, dpi=200)
    
    full_text = []
    for i, image in enumerate(images):
        print(f"  Processing page {i+1}/{len(images)}")
        text = pytesseract.image_to_string(image, lang='eng')
        full_text.append(f"\n--- Page {i+1} ---\n{text}")
    
    return "\n".join(full_text)

def ocr_image(image_path: str) -> str:
    """Extract text from image (PNG, JPG)"""
    image = Image.open(image_path)
    return pytesseract.image_to_string(image, lang='eng')