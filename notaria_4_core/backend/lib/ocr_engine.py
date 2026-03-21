import logging
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

logger = logging.getLogger(__name__)

# Try loading spaCy NLP
try:
    import spacy
    try:
        nlp = spacy.load("es_core_news_sm")
    except OSError:
        logger.warning("spaCy model 'es_core_news_sm' not found. NLP features disabled.")
        nlp = None
except ImportError:
    logger.warning("spaCy not installed. NLP features disabled.")
    nlp = None

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from a PDF document using a hybrid strategy.
    First, tries native text extraction via PyMuPDF (fitz).
    If the native text is too sparse (indicating a scanned image),
    falls back to OCR via pytesseract.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"Failed to open PDF with fitz: {e}")
        return ""

    full_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Strategy 1: Native Text Extraction
        native_text = page.get_text()

        # If there's enough text, we assume it's a native PDF.
        # Arbitrary threshold: if we extract less than 50 chars, maybe it's just artifacts on an image.
        if len(native_text.strip()) > 50:
            full_text.append(native_text)
            logger.info(f"Page {page_num}: Extracted native text.")
        else:
            # Strategy 2: OCR Fallback
            logger.info(f"Page {page_num}: Native text sparse. Attempting OCR.")
            # Render page to an image
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))

            # Use pytesseract to extract text from the rendered image
            try:
                # We specify Spanish language if available, fallback to default otherwise
                ocr_text = pytesseract.image_to_string(img, lang="spa")
            except Exception as ocr_err:
                logger.error(f"OCR failed for page {page_num}: {ocr_err}")
                try:
                    ocr_text = pytesseract.image_to_string(img)
                except Exception as e:
                    logger.error(f"Fallback OCR failed: {e}")
                    ocr_text = ""

            full_text.append(ocr_text)

    return "\n".join(full_text)

def analyze_text(text: str) -> dict:
    """
    Basic NLP analysis of the extracted text using spaCy if available.
    Returns a dictionary of extracted entities or metadata.
    """
    if not nlp:
        logger.info("NLP model not available. Returning empty analysis.")
        return {}

    # Process text with spaCy
    doc = nlp(text)

    # Simple example of entity extraction (just for demonstration)
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)

    return entities
