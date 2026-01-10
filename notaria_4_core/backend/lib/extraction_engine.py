import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Set tesseract path if needed, though Docker handles it globally
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

class ExtractionEngine:
    @staticmethod
    def extract_text_smart(pdf_bytes: bytes) -> str:
        """
        Extracts text from PDF bytes.
        Strategy:
        1. Try PyMuPDF (fast, native text).
        2. If result is empty or too short, fallback to Tesseract (OCR).
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""

        # Method 1: PyMuPDF Native
        for page in doc:
            text += page.get_text()

        # Heuristic: If text is very short, it might be a scan.
        if len(text.strip()) < 50:
            print("Native extraction failed or insufficient. Falling back to OCR.")
            return ExtractionEngine._extract_text_ocr(doc)

        return text

    @staticmethod
    def _extract_text_ocr(doc) -> str:
        """
        Internal method to run Tesseract on PDF pages.
        """
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()

            # Convert PyMuPDF Pixmap to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # Run Tesseract (Spanish)
            page_text = pytesseract.image_to_string(image, lang='spa')
            text += page_text + "\n"

        return text

class NLPEngine:
    def __init__(self):
        # In a real scenario, we load the fine-tuned model
        # self.nlp = spacy.load("es_core_news_lg")
        # For now, we stub this as we don't have the model file
        pass

    def extract_entities(self, text: str) -> dict:
        """
        Placeholder for spaCy entity extraction.
        Should return: {'vendedor': ..., 'adquirente': ..., 'monto': ...}
        """
        # TODO: Implement fine-tuned model inference
        return {
            "entities_found": [],
            "raw_text_snippet": text[:100] + "..."
        }
