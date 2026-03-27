import logging
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import re

logger = logging.getLogger(__name__)

# NLP setup
try:
    import spacy
    nlp = spacy.load("es_core_news_sm")
except (ImportError, OSError):
    nlp = None
    logger.warning("Spacy or model 'es_core_news_sm' not found. NLP features disabled.")

def extract_text_hybrid(pdf_bytes: bytes) -> dict:
    text = ""
    try:
        # Native text extraction using PyMuPDF (fitz)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text += page_text

        # If text is too sparse, try OCR as a fallback
        if len(text.strip()) < 50:
            text = ""
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img, lang="spa")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return {"error": str(e)}

    # Apply NLP + Regex if available
    extracted_data = {}
    if nlp:
        doc_nlp = nlp(text)
        # Use simple NER logic or just regexes as per instructions

    # Reinforce with deterministic Regex rules
    escritura_match = re.search(r"(?:ESCRITURA|INSTRUMENTO)\s+(?:NÚMERO|NO\.|NUM\.)?\s*(\d{1,5})", text, re.IGNORECASE)
    if escritura_match:
        extracted_data["numero_escritura"] = escritura_match.group(1)

    # Basic RFC extraction
    rfc_matches = re.findall(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}", text)
    if rfc_matches:
        extracted_data["rfcs_found"] = list(set(rfc_matches))

    return {
        "text_preview": text[:500],
        "extracted_data": extracted_data
    }
