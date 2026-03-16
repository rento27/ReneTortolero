import logging

logger = logging.getLogger(__name__)

def extract_text(pdf_bytes: bytes) -> str:
    """
    Hybrid extraction strategy: attempts native text extraction via PyMuPDF (fitz) first,
    and falls back to OCR via pytesseract on rendered images if the text density is low.
    Gracefully handles absence of es_core_news_sm spacy model.
    """
    # Stub implementation
    try:
        import spacy
        # Try to load model, handle absence gracefully
        try:
            nlp = spacy.load("es_core_news_sm")
        except OSError:
            logger.warning("es_core_news_sm spaCy model not found. NLP features disabled.")
    except ImportError:
        pass

    return "Extracted text stub"
