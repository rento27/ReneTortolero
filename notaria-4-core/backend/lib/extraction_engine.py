import fitz  # PyMuPDF
import pytesseract
import spacy
import re
import io
from PIL import Image

class ExtractionEngine:
    def __init__(self):
        # Load spaCy model. In production (Docker), this will be downloaded.
        # Fallback to a blank model or raise warning if not found locally for dev.
        try:
            self.nlp = spacy.load("es_core_news_lg")
        except OSError:
            print("Warning: spaCy model 'es_core_news_lg' not found. NLP features will be limited.")
            self.nlp = spacy.blank("es")

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """
        Strategy:
        1. Try extracting text directly (Digital Native PDF).
        2. If text is sparse (< 50 chars), render pages to images and use OCR (Scanned PDF).
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""

        # 1. Try Digital Extraction
        for page in doc:
            text += page.get_text()

        # 2. Check density. If low, assume scanned and use OCR.
        if len(text.strip()) < 50:
            print("Detected scanned document. Engaging Tesseract OCR...")
            text = "" # Reset
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Tesseract configuration for Spanish
                text += pytesseract.image_to_string(img, lang='spa')

        return text

    def extract_entities(self, text: str) -> dict:
        """
        Combines NLP (spaCy) and Regex to extract structured data.
        """
        clean_text = text.replace('\n', ' ')

        data = {
            "rfc": None,
            "escritura": None,
            "monto": None,
            "razon_social": None,
            "raw_text_snippet": clean_text[:200] + "..." # For debugging
        }

        # --- REGEX EXTRACTION (Deterministic) ---

        # RFC Pattern (Moral or Fisica)
        rfc_pattern = r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}"
        rfc_match = re.search(rfc_pattern, clean_text)
        if rfc_match:
            data["rfc"] = rfc_match.group(0)

        # Escritura Number Pattern
        # Updated to handle accented and unaccented 'Numero', and various abbreviations
        escritura_pattern = r"(?:ESCRITURA|INSTRUMENTO)\s+(?:NÚMERO|NUMERO|NO\.|NUM\.|#)?\s*(\d{1,5})"
        escritura_match = re.search(escritura_pattern, clean_text, re.IGNORECASE)
        if escritura_match:
            data["escritura"] = escritura_match.group(1)

        # Amount Pattern (Looks for money format e.g., $1,234.56)
        # This is simplistic; usually we look near "Precio" or "Operación"
        monto_pattern = r"\$\s?([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})"
        monto_matches = re.findall(monto_pattern, clean_text)
        if monto_matches:
            # Heuristic: The largest amount is likely the operation value
            montos = [float(m.replace(',', '')) for m in monto_matches]
            data["monto"] = max(montos)

        # --- NLP EXTRACTION (Probabilistic) ---
        doc = self.nlp(clean_text)

        # Attempt to find Organization names if RFC found
        if data["rfc"]:
             # Simple heuristic: Look for ORG entities near the RFC or specific keywords
             for ent in doc.ents:
                 if ent.label_ == "ORG" and len(ent.text) > 5:
                     # Remove common legal suffixes for the 'sanitized' version
                     # This is a basic implementation
                     sanitized = re.sub(r"\s+(S\.?A\.?|S\.?C\.?|S\.?R\.?L\.?|DE C\.?V\.?).*", "", ent.text, flags=re.IGNORECASE)
                     data["razon_social"] = sanitized.strip()
                     break # Take the first one for now

        return data
