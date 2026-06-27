import re
import logging
import io

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logger.warning("fitz (PyMuPDF) is not installed. Text extraction may not work.")

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None
    logger.warning("Pillow or pytesseract is not installed. OCR will be disabled.")

try:
    import spacy
    try:
        nlp = spacy.load("es_core_news_sm")
    except Exception as e:
        logger.warning(f"spaCy model 'es_core_news_sm' not found. NLP features disabled. {e}")
        nlp = None
except ImportError:
    spacy = None
    nlp = None
    logger.warning("spaCy is not installed. NLP features disabled.")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from a PDF file.
    Attempts native extraction first, falls back to OCR if text density is too low.
    """
    if not fitz:
        raise RuntimeError("PyMuPDF (fitz) is not available.")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_content = []

    for page in doc:
        page_text = page.get_text()
        text_content.append(page_text)

    full_text = "\n".join(text_content)

    # Simple heuristic: if we got very little text relative to the number of pages,
    # it's likely a scanned PDF and we need OCR.
    if len(full_text.strip()) < (len(doc) * 100) and pytesseract and Image:
        logger.info("Low text density detected. Falling back to OCR.")
        ocr_text = []
        for page in doc:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            # Spanish lang if tesseract-ocr-spa is installed
            page_ocr_text = pytesseract.image_to_string(img, lang="spa")
            ocr_text.append(page_ocr_text)
        full_text = "\n".join(ocr_text)

    return full_text

def extract_structured_data(text: str) -> dict:
    """
    Extracts structured data (like RFC and Escritura numbers) from raw text
    using regular expressions and optionally NLP.
    """
    data = {
        "escritura": None,
        "rfcs": [],
        "vendedores": [],
        "adquirientes": [],
        "inmuebles": [],
        "montos": []
    }

    # Extract Escritura using deterministic regex
    escritura_match = re.search(r"(?:ESCRITURA|INSTRUMENTO)\s+(?:NÚMERO|NO\.|NUM\.)?\s*(\d{1,5})", text, re.IGNORECASE)
    if escritura_match:
        data["escritura"] = escritura_match.group(1)

    # Extract RFCs using deterministic regex
    # Matches Persona Física (4 letters) and Persona Moral (3 letters) followed by 6 digits and 3 alphanumeric
    rfc_matches = re.findall(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}", text)
    data["rfcs"] = list(set(rfc_matches))  # remove duplicates

    # Use explicit string matching fallback logic if spaCy fails or is not available for full extraction
    if not nlp or not data.get("vendedores") or not data.get("adquirientes"):
        # Very simple heuristic logic based on keyword matching
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_upper = line.upper()
            if 'COMPARECE' in line_upper:
                # Naively assume the next few words are the vendor name
                parts = line.split('COMPARECE')
                if len(parts) > 1:
                    name_part = parts[1].strip()
                    if name_part:
                        data["vendedores"].append(name_part.split(',')[0].strip())
            elif 'COMPRA' in line_upper:
                # Naively assume the preceding or following words might be the acquirer
                parts = line.split('COMPRA')
                if len(parts) > 1:
                    name_part = parts[0].strip()
                    if name_part:
                        data["adquirientes"].append(name_part.split(',')[0].strip())

    # Stub for NLP
    if nlp:
        # We would use the custom `ner_notaria` spaCy model with a fallback to `es_core_news_lg` here
        # doc = nlp(text)
        # For now we'll stick to the basic regex and simple matches
        pass

    return data
