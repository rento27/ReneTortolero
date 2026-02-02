import fitz  # PyMuPDF
import pytesseract
import spacy
import os
from typing import Dict, Any

# Load spaCy model lazily
nlp = None

def get_nlp_model():
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("es_core_news_lg")
        except OSError:
            # Fallback or handle missing model during build/dev
            print("Warning: spacy model not found. Run 'python -m spacy download es_core_news_lg'")
            return None
    return nlp

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF using a hybrid approach:
    1. Try PyMuPDF (fitz) for digital text (fastest, accurate).
    2. If text is insufficient (scanned), use Tesseract OCR.
    """
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()

        # Heuristic: If text length is very low, it might be an image scan
        if len(text.strip()) < 50:
            print("Low text density detected. Falling back to OCR...")
            text = "" # Reset
            # TODO: Implement full Tesseract loop per page
            # This requires converting PDF pages to images first (e.g. using fitz.get_pixmap)
            # For simplicity in this scaffold, we just return what we have or a placeholder
            pass

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

    return text

def analyze_deed_text(text: str) -> Dict[str, Any]:
    """
    Uses NLP (spaCy) and Regex to extract structured data from the deed text.
    """
    model = get_nlp_model()
    if not model:
        return {"error": "NLP model not loaded"}

    doc = model(text)

    extracted_data = {
        "personas": [],
        "monto_operacion": None,
        "numero_escritura": None
    }

    # 1. Regex for Escritura Number
    # Pattern looks for "ESCRITURA" followed by digits
    import re
    escritura_match = re.search(r"(?:ESCRITURA|INSTRUMENTO)\s+(?:NÚMERO|NO\.|NUM\.)?\s*(\d{1,5})", text, re.IGNORECASE)
    if escritura_match:
        extracted_data["numero_escritura"] = escritura_match.group(1)

    # 2. Named Entity Recognition (NER) for Persons (PER)
    for ent in doc.ents:
        if ent.label_ == "PER":
            extracted_data["personas"].append(ent.text)

    return extracted_data
