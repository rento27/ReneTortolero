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
        nlp = spacy.load("ner_notaria")
    except Exception as e:
        logger.warning(f"Custom spaCy model 'ner_notaria' not found. Attempting fallback to 'es_core_news_lg'. {e}")
        try:
            nlp = spacy.load("es_core_news_lg")
        except Exception as e2:
            logger.warning(f"Fallback spaCy model 'es_core_news_lg' not found. NLP features disabled. {e2}")
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

    nlp_populated = False
    if nlp:
        doc = nlp(text)
        # Assuming the custom model returns specific labels for 'VENDEDOR', 'ADQUIRIENTE', 'INMUEBLE', 'MONTO'
        for ent in doc.ents:
            if ent.label_ == "VENDEDOR":
                data["vendedores"].append(ent.text)
                nlp_populated = True
            elif ent.label_ == "ADQUIRIENTE":
                data["adquirientes"].append(ent.text)
                nlp_populated = True
            elif ent.label_ == "INMUEBLE":
                data["inmuebles"].append(ent.text)
                nlp_populated = True
            elif ent.label_ == "MONTO":
                data["montos"].append(ent.text)
                nlp_populated = True

    # Fallback to explicit string matching logic looking for keywords COMPARECE and COMPRA
    if not data["vendedores"] and not data["adquirientes"]:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "COMPARECE" in line.upper():
                # Extract the rest of the line or next lines, simplistic fallback
                data["vendedores"].append(line.replace("COMPARECE", "").strip())
            if "COMPRA" in line.upper():
                data["adquirientes"].append(line.replace("COMPRA", "").strip())

    return data
