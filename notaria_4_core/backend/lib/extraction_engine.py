import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import spacy

# Fallback to empty model if not present, to ensure robustness during dev
try:
    nlp = spacy.load("es_core_news_lg")
except OSError:
    nlp = spacy.blank("es")

class ExtractionEngine:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        """
        Extracts text from a PDF or Image using a hybrid approach.
        1. PyMuPDF (fast, digital text).
        2. Tesseract (slow, OCR) if text is insufficient.
        """
        text = ""

        # Determine file type
        if filename.lower().endswith(".pdf"):
            text = ExtractionEngine._extract_from_pdf(file_bytes)

        # If text is too short (likely scanned PDF or image), try OCR
        if len(text.strip()) < 50:
            text = ExtractionEngine._extract_via_ocr(file_bytes, filename)

        return text

    @staticmethod
    def _extract_from_pdf(file_bytes: bytes) -> str:
        text = ""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text()
        except Exception as e:
            print(f"Error reading PDF stream: {e}")
        return text

    @staticmethod
    def _extract_via_ocr(file_bytes: bytes, filename: str) -> str:
        text = ""
        try:
            if filename.lower().endswith(".pdf"):
                # Convert PDF pages to images
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    text += pytesseract.image_to_string(image, lang='spa')
            else:
                # Image file
                image = Image.open(io.BytesIO(file_bytes))
                text += pytesseract.image_to_string(image, lang='spa')
        except Exception as e:
            print(f"Error in OCR: {e}")
        return text

    @staticmethod
    def extract_entities(text: str) -> dict:
        """
        Uses spaCy to extract entities (PER, LOC, ORG, MONEY).
        """
        doc = nlp(text)
        entities = {
            "PER": [],
            "ORG": [],
            "LOC": [],
            "MONEY": [] # Default model might need custom training for MONEY/PRICE in deeds
        }

        for ent in doc.ents:
            if ent.label_ in entities:
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)

        return entities
