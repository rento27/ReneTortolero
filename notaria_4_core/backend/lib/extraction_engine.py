import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

# Setup tesseract path if not in standard path (In Docker it is standard)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

class ExtractionEngine:
    def __init__(self):
        # We might initialize spacy model here in a real scenario
        # self.nlp = spacy.load("es_core_news_lg")
        pass

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Hybrid extraction strategy:
        1. Try digital extraction (PyMuPDF).
        2. If text is sparse, fallback to OCR (Tesseract).
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""

        for page in doc:
            text = page.get_text()
            if len(text.strip()) > 50:
                # Digital text found
                full_text += text + "\n"
            else:
                # Fallback to OCR for this page
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                ocr_text = pytesseract.image_to_string(image, lang='spa')
                full_text += ocr_text + "\n"

        return full_text

    def parse_entities(self, text: str) -> dict:
        """
        Extracts entities using Regex as a robust fallback to NLP.
        """
        entities = {}

        # Regex Patterns based on architectural requirements
        patterns = {
            # Matches "ESCRITURA 12345" or "INSTRUMENTO NUM. 12345"
            "numero_escritura": r"(?:ESCRITURA|INSTRUMENTO)\s+(?:N[UÚ]MERO|NO\.|NUM\.)?\s*(\d{1,5})",

            # Matches standard RFCs (Personas Físicas & Morales)
            "rfcs": r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}",

            # Matches currency values e.g. $1,234.56
            "montos_detectados": r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
        }

        for key, pattern in patterns.items():
            # Find all matches
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # De-duplicate and store
                entities[key] = list(set(matches))

        entities["raw_text_length"] = len(text)
        return entities
