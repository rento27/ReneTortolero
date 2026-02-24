import fitz  # PyMuPDF
import re
import spacy
from typing import Dict, Any, Optional
import io
import logging
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    logger.warning("es_core_news_sm not found, NLP features disabled")
    nlp = None

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes using PyMuPDF (fitz) first.
    If text is minimal (indicating a scanned document), falls back to Tesseract OCR.
    """
    text = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # 1. Try native text extraction
        for page in doc:
            text += page.get_text() + "\n"

        # 2. Heuristic check: If text is very short relative to page count, it's likely scanned.
        # Threshold: < 50 chars per page on average?
        if len(text.strip()) < 50 * len(doc):
            logger.info("Text extraction yielded minimal results. Attempting OCR fallback.")
            ocr_text = ""
            if pytesseract:
                for page in doc:
                    # Render page to image
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # Run Tesseract
                    # lang='spa' assumes Spanish language pack installed
                    try:
                        page_ocr = pytesseract.image_to_string(img, lang='spa')
                        ocr_text += page_ocr + "\n"
                    except Exception as e:
                        logger.error(f"Tesseract Error on page {page.number}: {e}")

            if len(ocr_text.strip()) > len(text.strip()):
                return ocr_text

        return text

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_structured_data(text: str) -> Dict[str, Any]:
    """
    Extracts structured data using Regex and NLP.
    """
    data = {}

    # 1. Regex Extraction (Deterministic)

    # Escritura Number: "ESCRITURA PUBLICA NUMERO 12,345"
    escritura_match = re.search(r"(?:ESCRITURA|INSTRUMENTO)\s+(?:PÚBLICA|PUBLICA)?\s*(?:NÚMERO|NO\.|NUM\.)?\s*(\d{1,6})", text, re.IGNORECASE)
    if escritura_match:
        data['numero_escritura'] = escritura_match.group(1)

    # Monto: "$ 1,234,567.00" or similar
    # Look for currency format
    monto_match = re.search(r"\$\s?([0-9,]+\.\d{2})", text)
    if monto_match:
        # Clean up commas
        try:
            monto_str = monto_match.group(1).replace(",", "")
            data['monto_operacion'] = float(monto_str)
        except ValueError:
            pass

    # RFC: Standard Pattern
    rfc_match = re.search(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}", text)
    if rfc_match:
        data['rfc_detectado'] = rfc_match.group(0)

    # 2. NLP Extraction (Probabilistic)
    if nlp:
        doc = nlp(text[:5000]) # Process first 5k chars to save time

        # Extract PERSON entities
        persons = [ent.text for ent in doc.ents if ent.label_ == "PER"]
        data['personas_detectadas'] = list(set(persons)) # Unique

        # Extract ORG entities
        orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        data['organizaciones_detectadas'] = list(set(orgs))

    return data
