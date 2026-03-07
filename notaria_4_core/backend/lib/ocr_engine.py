import logging
import fitz # PyMuPDF
import pytesseract
from PIL import Image
import io

logger = logging.getLogger(__name__)

nlp = None
try:
    import spacy
    nlp = spacy.load("es_core_news_sm")
except OSError:
    logger.warning("es_core_news_sm spaCy model not found. NLP features will be disabled.")
except ImportError:
    logger.warning("spaCy not installed. NLP features will be disabled.")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Hybrid extraction strategy for PDF documents.
    1. Fast path: Tries to extract text directly via PyMuPDF (fitz).
    2. Slow path: If the density of text extracted natively is very low, falls back to pytesseract OCR.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # Simple heuristic to determine if OCR is needed: less than 50 characters extracted usually indicates a scanned image.
    if len(text.strip()) < 50:
        logger.info("Low text density detected from fitz. Falling back to pytesseract OCR.")
        text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += pytesseract.image_to_string(img, lang="spa")

    return text
