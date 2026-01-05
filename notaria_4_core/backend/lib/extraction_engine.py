import spacy
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

class ExtractionEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("es_core_news_lg")
            # Load custom NER model if available
            # self.nlp_custom = spacy.load("ner_notaria")
        except OSError:
            print("Warning: spacy model not found. Run 'python -m spacy download es_core_news_lg'")
            self.nlp = spacy.blank("es")

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extracts text using a hybrid approach:
        1. Try direct extraction (PyMuPDF)
        2. If text is sparse, use OCR (Tesseract) on images
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""

        for page in doc:
            text = page.get_text()
            if len(text) > 50:  # Threshold to decide if it's a digital PDF
                full_text += text
            else:
                # Render page to image for OCR
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                ocr_text = pytesseract.image_to_string(img, lang='spa')
                full_text += ocr_text

        return full_text

    def extract_entities(self, text: str) -> dict:
        """
        Uses NLP to extract entities (VENDEDOR, ADQUIRENTE, INMUEBLE, MONTO).
        Currently a placeholder using the generic model.
        """
        doc = self.nlp(text)
        entities = {
            "PER": [], # Persons
            "LOC": [], # Locations
            "ORG": [], # Organizations
            "MISC": []
        }

        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)

        # TODO: Implement rule-based Regex extraction here for strict fields (Escritura #, RFC)

        return entities
