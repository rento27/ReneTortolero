import base64
import logging
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
except ImportError:
    spacy = None

# Attempt to load the model gracefully
nlp = None
if spacy:
    try:
        nlp = spacy.load("es_core_news_sm")
    except OSError:
        logger.warning("spacy model 'es_core_news_sm' not found. NLP features disabled.")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Hybrid extraction strategy: attempts native text extraction via fitz (PyMuPDF) first.
    Falls back to pytesseract (OCR) on rendered images if the text density is low.
    """
    text = ""
    if not fitz:
        logger.error("fitz (PyMuPDF) not installed.")
        return text

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        for page in doc:
            page_text = page.get_text()
            if len(page_text.strip()) > 50:
                text += page_text + "\n"
            else:
                # Text density low, fallback to OCR
                if pytesseract and Image:
                    try:
                        pix = page.get_pixmap()
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        ocr_text = pytesseract.image_to_string(img, lang="spa")
                        text += ocr_text + "\n"
                    except Exception as e:
                        logger.warning(f"OCR failed for a page: {e}")
                else:
                    logger.warning("OCR (pytesseract/Pillow) not available, skipping page with low text density.")

        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""


def process_text_with_nlp(text: str) -> dict:
    """
    Uses spacy to process the text.
    Returns a dictionary with extracted entities if the model is available.
    """
    result = {"text": text, "entities": []}
    if not nlp:
        return result

    try:
        doc = nlp(text)
        result["entities"] = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    except Exception as e:
        logger.error(f"Error processing text with NLP: {e}")

    return result


def extract_data(file_base64: str) -> dict:
    """
    Main entry point for data extraction.
    """
    try:
        pdf_bytes = base64.b64decode(file_base64)
        text = extract_text_from_pdf(pdf_bytes)
        return process_text_with_nlp(text)
    except Exception as e:
        logger.error(f"Failed to extract data: {e}")
        return {"error": str(e)}
