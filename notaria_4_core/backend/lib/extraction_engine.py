import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import spacy
from typing import Dict, Any, Optional

class ExtractionEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("es_core_news_lg")
        except OSError:
            # Fallback if model is not present (e.g., in dev or build phase)
            print("Warning: es_core_news_lg not found. Using blank 'es' model.")
            self.nlp = spacy.blank("es")

    def extract_text(self, pdf_path: str) -> str:
        """
        Extracts text from a PDF using a two-layer strategy:
        1. Fast Layer: PyMuPDF (fitz) for digital text.
        2. Deep Layer: Tesseract OCR for scanned images.
        """
        text = ""
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()

            # Heuristic: If page text is sparse (likely scanned), use OCR
            if len(page_text.strip()) < 50:
                # Render page to image
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                try:
                    # Use Tesseract
                    ocr_text = pytesseract.image_to_string(img, lang='spa')
                    text += ocr_text + "\n"
                except Exception as e:
                    print(f"OCR failed for page {page_num}: {e}")
                    # Fallback to whatever fitz got
                    text += page_text + "\n"
            else:
                text += page_text + "\n"

        return text

    def parse_entities(self, text: str) -> Dict[str, Any]:
        """
        Extracts entities using NLP and Regex.
        """
        doc = self.nlp(text)

        entities = {
            "numero_escritura": None,
            "rfcs": [],
            "montos": []
        }

        # 1. Extract Numero Escritura (Regex)
        # Matches: ESCRITURA NUMERO 12345 or INSTRUMENTO 12345
        escritura_pattern = r"(?:ESCRITURA|INSTRUMENTO)\s+(?:N[UÚ]MERO|NO\.|NUM\.)?\s*(\d{1,5})"
        match = re.search(escritura_pattern, text, re.IGNORECASE)
        if match:
            entities["numero_escritura"] = match.group(1)

        # 2. Extract RFCs (Regex)
        rfc_pattern = r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}"
        entities["rfcs"] = list(set(re.findall(rfc_pattern, text)))

        # 3. Extract Montos (Regex/NLP)
        # Simple regex for currency
        monto_pattern = r"\$\s?[\d,]+\.\d{2}"
        entities["montos"] = re.findall(monto_pattern, text)

        return entities
