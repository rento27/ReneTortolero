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
    io = None

try:
    import spacy
    try:
        nlp = spacy.load("es_core_news_sm")
    except Exception:
        logger.warning("spaCy model 'es_core_news_sm' not found. NLP features will be disabled.")
        nlp = None
except ImportError:
    spacy = None
    nlp = None

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Hybrid extraction strategy.
    Attempts native text extraction via PyMuPDF first.
    Falls back to Tesseract OCR if text density is low (e.g., scanned PDF).
    """
    if not fitz:
        logger.error("fitz (PyMuPDF) is not available.")
        return ""

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"Error opening PDF: {e}")
        return ""

    full_text = ""
    total_text_length = 0

    # Pass 1: Native Extraction
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        full_text += text + "\n"
        total_text_length += len(text.strip())

    # Density Check
    # If the document has pages but very little selectable text, it's likely a scan.
    # We define a rough threshold of 50 characters per page average.
    avg_chars_per_page = total_text_length / len(doc) if len(doc) > 0 else 0

    if avg_chars_per_page < 50 and pytesseract and Image:
        logger.info("Low text density detected. Falling back to OCR.")
        ocr_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # upscale for OCR
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            # Run Tesseract
            text = pytesseract.image_to_string(img, lang="spa")
            ocr_text += text + "\n"
        full_text = ocr_text

    doc.close()
    return full_text

def analyze_text(text: str) -> dict:
    """
    Analyzes extracted text using spaCy (if available).
    Returns basic structured info.
    """
    result = {"raw_text": text, "entities": []}
    if nlp and text.strip():
        # Truncate text if it's too long for the model to avoid memory errors
        max_len = 100000
        doc = nlp(text[:max_len])
        for ent in doc.ents:
            result["entities"].append({
                "text": ent.text,
                "label": ent.label_
            })
    return result

def process_pdf_base64(b64_string: str) -> dict:
    """
    Decodes base64 PDF and extracts/analyzes text.
    """
    try:
        pdf_bytes = base64.b64decode(b64_string)
        text = extract_text_from_pdf(pdf_bytes)
        return analyze_text(text)
    except Exception as e:
        logger.error(f"Error processing base64 PDF: {e}")
        return {"error": str(e)}
