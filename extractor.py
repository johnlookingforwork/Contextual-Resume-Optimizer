import fitz  # PyMuPDF
from pydantic import BaseModel, Field
from typing import List, Optional

# This Pydantic model defines the 'Schema' for your Ph.D. journal
class ResumeData(BaseModel):
    raw_text: str
    page_count: int
    metadata: dict

def extract_resume_text(pdf_path: str) -> ResumeData:
    """Extracts text and metadata from a PDF file."""
    doc = fitz.open(pdf_path)
    full_text = ""
    
    for page in doc:
        full_text += page.get_text() + "\n"
    
    return ResumeData(
        raw_text=full_text,
        page_count=len(doc),
        metadata=doc.metadata
    )

# Quick Test
if __name__ == "__main__":
    # Replace with your actual resume filename
    data = extract_resume_text("data/my_resume.pdf") 
    print(f"Extracted {data.page_count} pages.")
    print(data.raw_text[:500]) # Print first 500 chars to verify