import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import spacy
import io

class ExtractionEngine:
    def __init__(self, model_name="es_core_news_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            # Fallback if model not found during dev
            self.nlp = spacy.blank("es")

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extracts text from a PDF using a hybrid approach:
        1. Try direct text extraction (PyMuPDF).
        2. If text is sparse (scanned document), use OCR (Tesseract).
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""

        for page_num, page in enumerate(doc):
            text = page.get_text()

            # Simple heuristic: if less than 50 chars, assume it's scanned
            if len(text.strip()) < 50:
                # Render page to image for OCR
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))

                # Run Tesseract
                ocr_text = pytesseract.image_to_string(img, lang="spa")
                full_text += ocr_text + "\n"
            else:
                full_text += text + "\n"

        return full_text

    def extract_entities(self, text: str) -> dict:
        """
        Uses spaCy and Regex to identify key entities:
        - Instrument Number
        - RFCs
        - Amounts
        """
        doc = self.nlp(text)

        entities = {
            "instrument_number": None,
            "rfcs": [],
            "amounts": []
        }

        # Regex for specific structured data
        import re

        # Instrument Number (simplified regex based on blueprint)
        inst_match = re.search(r"(?:ESCRITURA|INSTRUMENTO)\s+(?:NÚMERO|NO\.|NUM\.)?\s*(\d{1,5})", text, re.IGNORECASE)
        if inst_match:
            entities["instrument_number"] = inst_match.group(1)

        # RFC Regex
        rfcs = re.findall(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}", text)
        entities["rfcs"] = list(set(rfcs)) # Deduplicate

        return entities
