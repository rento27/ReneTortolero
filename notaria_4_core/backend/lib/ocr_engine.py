import logging
from typing import Optional

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
    nlp = spacy.load("es_core_news_sm")
except OSError:
    logging.warning("es_core_news_sm spaCy model not found. NLP features will be disabled.")
    nlp = None
except ImportError:
    logging.warning("spaCy not found. NLP features will be disabled.")
    nlp = None

logger = logging.getLogger(__name__)

def extract_text_hybrid(file_bytes: bytes) -> str:
    """
    Attempts native text extraction via PyMuPDF first.
    Falls back to pytesseract OCR if text density is low.
    """
    if not fitz:
        logger.error("fitz (PyMuPDF) not installed.")
        return ""

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        # Very simple density check: If less than 50 characters, assume it's an image pdf
        if len(text.strip()) < 50 and pytesseract:
            logger.info("Low text density detected. Falling back to OCR.")
            ocr_text = ""
            for i in range(len(doc)):
                page = doc[i]
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                ocr_text += pytesseract.image_to_string(img, lang="spa")
            return ocr_text

        return text
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""

def process_text_nlp(text: str) -> dict:
    """
    Processes the extracted text using spaCy to find entities.
    Returns a dictionary of found entities.
    """
    if not nlp:
        logger.info("NLP model not available. Returning empty extraction.")
        return {}

    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)

    return entities
