import logging
import fitz
import pytesseract
from PIL import Image
import io

logger = logging.getLogger(__name__)

nlp = None
try:
    import spacy
    nlp = spacy.load("es_core_news_sm")
except OSError:
    logger.warning("Spacy model 'es_core_news_sm' not found. NLP features will be disabled.")
except ImportError:
    logger.warning("spacy library not found. NLP features will be disabled.")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Hybrid extraction strategy: attempts native text extraction via fitz (PyMuPDF) first.
    Falls back to pytesseract if text density is low.
    """
    text = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            page_text = page.get_text()
            text += page_text + "\n"

        # Very simple text density check to determine if OCR is needed
        # If there are fewer than 100 characters per page on average, it might be a scanned document
        if len(text.strip()) < (len(doc) * 100):
            logger.info("Low text density detected. Falling back to OCR.")
            text = ""
            for page in doc:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                text += pytesseract.image_to_string(img, lang='spa') + "\n"

        doc.close()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise e

    return text

def extract_entities(text: str) -> dict:
    """
    Extracts entities using NLP if available.
    """
    if not nlp:
        logger.warning("NLP features are disabled. Entity extraction will return empty dictionary.")
        return {}

    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        entities[ent.label_] = entities.get(ent.label_, []) + [ent.text]

    return entities
