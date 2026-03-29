import logging
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

# Attempt to load spaCy model
try:
    import spacy
    try:
        nlp = spacy.load("es_core_news_sm")
    except OSError:
        logger.warning("spaCy model 'es_core_news_sm' not found. NLP features will be disabled.")
        nlp = None
except ImportError:
    logger.warning("spaCy not installed. NLP features will be disabled.")
    nlp = None

# Deterministic Regex patterns
REGEX_ESCRITURA = re.compile(r"(?:ESCRITURA|INSTRUMENTO)\s+(?:NÚMERO|NO\.|NUM\.)?\s*(\d{1,5})", re.IGNORECASE)
REGEX_RFC = re.compile(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}", re.IGNORECASE)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF. Tries PyMuPDF (fast) first.
    If text density is too low (likely scanned), falls back to OCR via pytesseract.
    """
    text = ""
    try:
        # 1. Native Text Extraction (PyMuPDF)
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()

        # If very little text is extracted, it might be an image-only PDF
        if len(text.strip()) < 50:
            logger.info("Low text density with PyMuPDF. Falling back to OCR.")
            text = _extract_text_ocr(pdf_path)

    except Exception as e:
        logger.error(f"Error extracting text with PyMuPDF: {e}. Falling back to OCR.")
        text = _extract_text_ocr(pdf_path)

    return text

def _extract_text_ocr(pdf_path: str) -> str:
    """
    Extracts text using pytesseract OCR from rendered images.
    """
    text = ""
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img, lang="spa")
    except Exception as e:
        logger.error(f"Error during OCR extraction: {e}")
    return text

def extract_data_from_pdf(pdf_path: str) -> dict:
    """
    Extracts relevant data from the PDF using hybrid text extraction, NLP, and regex.
    """
    text = extract_text_from_pdf(pdf_path)

    data = {
        "escritura": None,
        "rfcs": [],
        "raw_text_snippet": text[:500] + "..." if len(text) > 500 else text
    }

    # Deterministic Extraction
    escritura_match = REGEX_ESCRITURA.search(text)
    if escritura_match:
        data["escritura"] = escritura_match.group(1)

    data["rfcs"] = list(set(REGEX_RFC.findall(text)))

    # NLP Extraction
    if nlp:
        doc = nlp(text)
        # Note: In a fully trained scenario, we would extract custom entities here
        # (e.g. VENDEDOR, ADQUIRENTE, INMUEBLE) using a custom ner_notaria model.
        # For now, we stub this out or do basic NER if applicable.
        pass

    return data
