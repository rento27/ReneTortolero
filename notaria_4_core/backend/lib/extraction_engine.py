import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

class ExtractionEngine:
    def __init__(self):
        # Initialize NLP models here if needed
        pass

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extracts text from PDF bytes.
        Tries fitz (digital text) first.
        Falls back to Tesseract (OCR) if text is insufficient.
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""

        # Try digital extraction
        for page in doc:
            text += page.get_text()

        # Heuristic: If text length is very short relative to pages, it might be scanned
        if len(text.strip()) < 50:
            text = self._ocr_extraction(doc)

        return text

    def _ocr_extraction(self, doc) -> str:
        text = ""
        for page in doc:
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            text += pytesseract.image_to_string(image, lang='spa')
        return text
