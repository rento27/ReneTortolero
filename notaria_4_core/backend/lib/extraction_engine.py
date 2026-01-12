import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

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
        Placeholder for NLP extraction logic using spaCy.
        Returns a dictionary of extracted fields.
        """
        # TODO: Implement spaCy entity extraction
        return {
            "raw_text_length": len(text)
        }
