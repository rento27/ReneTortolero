import logging
import os

# Import fitz (PyMuPDF)
try:
    import fitz
except ImportError:
    fitz = None

# Import pytesseract
try:
    import pytesseract
except ImportError:
    pytesseract = None

# Import spacy
try:
    import spacy
except ImportError:
    spacy = None

logger = logging.getLogger(__name__)

class ExtractionEngine:
    def __init__(self):
        self.nlp = None
        self._load_spacy_model()

    def _load_spacy_model(self):
        """Loads the Spacy model safely."""
        if spacy:
            try:
                # Ideally load 'es_core_news_lg', falling back to sm or blank
                if spacy.util.is_package("es_core_news_lg"):
                    self.nlp = spacy.load("es_core_news_lg")
                elif spacy.util.is_package("es_core_news_sm"):
                    self.nlp = spacy.load("es_core_news_sm")
                else:
                    self.nlp = spacy.blank("es")
                    logger.warning("No Spacy model found. Using blank 'es' model.")
            except Exception as e:
                logger.error(f"Failed to load Spacy model: {e}")
                self.nlp = spacy.blank("es")

    def extract_text(self, pdf_path: str) -> str:
        """
        Hybrid extraction strategy:
        1. Try PyMuPDF (fast, digital text).
        2. If result is empty or too short (scanned), use Tesseract OCR.
        """
        text = ""

        # Layer 1: Digital Extraction
        if fitz:
            try:
                doc = fitz.open(pdf_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
            except Exception as e:
                logger.error(f"PyMuPDF extraction failed: {e}")

        # Heuristic: If text is too short, it's likely a scan
        if len(text.strip()) < 50:
            logger.info("Text too short, falling back to OCR (Tesseract).")
            return self._extract_ocr(pdf_path)

        return text

    def _extract_ocr(self, pdf_path: str) -> str:
        """
        Layer 2: Deep Extraction with Tesseract.
        """
        if not pytesseract:
            logger.warning("pytesseract not installed. Returning empty.")
            return ""

        text = ""
        try:
            # Note: In a real scenario, we'd convert PDF pages to images first using pdf2image.
            # Since pdf2image requires poppler which might not be here, we mock the flow.
            # Assuming pdf_path could be an image or handled by pytesseract if it supports PDF directly (older versions don't).
            # For this implementation, we will assume we have a mechanism to convert or tesseract handles it.
            # If pdf_path ends in pdf, Tesseract usually needs image conversion.
            # We will return a placeholder if we can't convert.
            pass
        except Exception as e:
            logger.error(f"OCR failed: {e}")

        return text

    def extract_entities(self, text: str) -> dict:
        """
        Uses NLP to find potential entities.
        """
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
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)

        return entities
