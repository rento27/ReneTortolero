import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
    from PIL import Image
    import io
except ImportError:
    pytesseract = None
    Image = None

try:
    import spacy
    try:
        nlp = spacy.load("es_core_news_sm")
    except Exception:
        logger.warning("es_core_news_sm spacy model not found. NLP features will be disabled.")
        nlp = None
except ImportError:
    spacy = None
    nlp = None

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Hybrid extraction strategy: attempts native text extraction via fitz (PyMuPDF) first.
    Falls back to pytesseract (OCR) on rendered images if text density is low.
    """
    if not fitz:
        logger.warning("fitz (PyMuPDF) is not installed. Returning empty string.")
        return ""

    text_extracted = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            text_extracted += page_text + "\n"

        # If text density is suspiciously low, assume it's a scanned image and fallback to OCR
        if len(text_extracted.strip()) < 100 and pytesseract and Image:
            logger.info("Low text density detected. Falling back to pytesseract OCR.")
            text_extracted = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render page to an image
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                page_text = pytesseract.image_to_string(img, lang="spa")
                text_extracted += page_text + "\n"

        doc.close()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")

    return text_extracted

def analyze_text(text: str) -> dict:
    """
    Basic NLP and Regex analysis of text.
    Gracefully degrades if NLP is not available.
    """
    results = {
        "entities": [],
        "rfc_found": []
    }

    # Regex fallback
    rfc_pattern = re.compile(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}")
    results["rfc_found"] = list(set(rfc_pattern.findall(text.upper())))

    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            results["entities"].append({
                "text": ent.text,
                "label": ent.label_
            })
    else:
        logger.debug("NLP model missing, skipping entity extraction.")

    return results
