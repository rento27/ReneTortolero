import fitz  # PyMuPDF
import pytesseract
import spacy
from typing import Optional

class ExtractionEngine:
    def __init__(self, model_path: str = "es_core_news_lg"):
        try:
            self.nlp = spacy.load(model_path)
        except OSError:
            print(f"Warning: Model {model_path} not found. NLP features disabled.")
            self.nlp = None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Hybrid extraction: Tries PyMuPDF first, falls back to Tesseract OCR.
        """
        text = ""
        try:
            # 1. Try Digital Extraction
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()

            # 2. Heuristic: If text is too short, assume scanned
            if len(text.strip()) < 50:
                raise ValueError("Insufficient text found, switching to OCR")

        except Exception as e:
            print(f"Digital extraction failed: {e}. Attempting OCR...")
            # 3. Fallback to OCR: Render pages to images using PyMuPDF (pixmap) and pass to Tesseract
            text = ""
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=300) # High DPI for better OCR

                    # Convert fitz Pixmap to bytes for pytesseract
                    # Note: In a real environment with PIL/Pillow we might convert pix.tobytes() to an Image object.
                    # pytesseract.image_to_string accepts image paths or numpy arrays or bytes (if valid).
                    # Since we don't have PIL listed explicitly in deps but fitz is here, let's assume we can save temp or pass bytes.
                    # For stability in this environment without full PIL setup verification:
                    # We will create a temporary image file.

                    temp_img = f"/tmp/page_{page_num}.png"
                    pix.save(temp_img)

                    page_text = pytesseract.image_to_string(temp_img, lang='spa')
                    text += page_text + "\n"

            except Exception as ocr_e:
                print(f"OCR Failed: {ocr_e}")
                text = "[OCR Failed]"

        return text

    def extract_entities(self, text: str):
        if not self.nlp:
            return {}

        doc = self.nlp(text)
        entities = {
            "PERSON": [],
            "ORG": [],
            "LOC": []
        }

        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)

        return entities
