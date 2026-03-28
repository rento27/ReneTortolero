import logging

logger = logging.getLogger(__name__)

nlp_model = None
try:
    import spacy
    nlp_model = spacy.load("es_core_news_sm")
except OSError:
    logger.warning("Spacy model 'es_core_news_sm' not found. NLP features will be disabled.")
except ImportError:
    logger.warning("Spacy library not found. NLP features will be disabled.")

def extract_from_pdf(pdf_bytes: bytes) -> str:
    """
    Hybrid extraction strategy. Tries native text extraction via PyMuPDF first,
    and falls back to pytesseract OCR if text density is low.
    """
    text = ""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text()

        # If native extraction yielded sufficient text, return it
        if len(text.strip()) > 100:
            return text

        logger.info("Native extraction yielded little text. Falling back to OCR.")
    except Exception as e:
        logger.info(f"Native extraction failed: {e}. Falling back to OCR.")

    # Fallback to OCR using pytesseract and pdf2image
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        from PIL import Image

        images = convert_from_bytes(pdf_bytes)
        ocr_text = ""
        for image in images:
            ocr_text += pytesseract.image_to_string(image, lang="spa")
        return ocr_text
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return text # return what we got from native if anything
