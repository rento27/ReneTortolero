import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import fitz # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
    from PIL import Image
    import io
except ImportError:
    pytesseract = None

try:
    import spacy
    try:
        nlp = spacy.load("es_core_news_sm")
    except OSError:
        logger.warning("Spacy model 'es_core_news_sm' not found. NLP features will be disabled.")
        nlp = None
except ImportError:
    nlp = None


def extract_text_hybrid(pdf_bytes: bytes) -> str:
    """
    Attempts native text extraction via PyMuPDF first.
    Falls back to Tesseract OCR if text density is low (indicating a scanned document).
    """
    if not fitz:
        logger.warning("fitz (PyMuPDF) not available, cannot process PDF.")
        return ""

    text_extracted = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Simple heuristic: if less than 50 chars, might be a scanned image
            if len(text.strip()) < 50:
                if pytesseract:
                    logger.info(f"Page {page_num} seems scanned. Falling back to OCR.")
                    # Get image of page
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    ocr_text = pytesseract.image_to_string(img, lang="spa")
                    text_extracted.append(ocr_text)
                else:
                    logger.warning(f"Page {page_num} seems scanned, but pytesseract is not available.")
            else:
                text_extracted.append(text)

        return "\n".join(text_extracted)
    except Exception as e:
        logger.error(f"Error during PDF text extraction: {e}")
        return ""
