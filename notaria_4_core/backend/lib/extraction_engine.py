import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os

# Ensure Tesseract is in the path or configured (ENV usually handles this)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from a PDF file using a hybrid approach:
    1. Try PyMuPDF (fitz) for digital text.
    2. Fallback to OCR (Tesseract) for scanned images if text is insufficient.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()

        # Heuristic: If text is very sparse (e.g., < 50 chars), it's likely a scan
        if len(text.strip()) < 50:
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            # Use Spanish model for OCR
            ocr_text = pytesseract.image_to_string(image, lang='spa')
            full_text += ocr_text + "\n"
        else:
            full_text += text + "\n"

    return full_text

def extract_entities(text: str):
    """
    Uses spaCy to extract named entities (PER, ORG, LOC).
    Placeholder for the fine-tuned model logic.
    """
    try:
        import spacy
        # In production, load the fine-tuned model 'ner_notaria'
        # nlp = spacy.load("ner_notaria")
        nlp = spacy.load("es_core_news_lg")
        doc = nlp(text)

        entities = {
            "persons": [ent.text for ent in doc.ents if ent.label_ == "PER"],
            "orgs": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
            "locs": [ent.text for ent in doc.ents if ent.label_ == "LOC"],
        }
        return entities
    except OSError:
        # Fallback if model not found during dev
        print("Warning: spaCy model not found.")
        return {}
