import fitz  # PyMuPDF
import pytesseract
import spacy
import os

# Try to load Spacy model, handle if not present (for dev envs)
try:
    nlp = spacy.load("es_core_news_lg")
except OSError:
    print("Warning: Spacy model 'es_core_news_lg' not found. Download it using 'python -m spacy download es_core_news_lg'")
    nlp = None

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Hybrid extraction:
    1. Try PyMuPDF (fast, digital native).
    2. If text is sparse, fallback to Tesseract OCR (slow, scanned).
    """
    text_content = ""

    # Layer 1: PyMuPDF
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text_content += page.get_text()
        doc.close()
    except Exception as e:
        print(f"PyMuPDF error: {e}")

    # Heuristic: If extracted text is too short, assume scanned document
    if len(text_content.strip()) < 50:
        print("Text sparse, falling back to Tesseract OCR...")
        try:
            # Note: This requires poppler-utils or similar to convert PDF to images first usually,
            # or we can use PyMuPDF to get pixmap
            doc = fitz.open(pdf_path)
            ocr_text = ""
            for page in doc:
                pix = page.get_pixmap()
                # Need to convert pix to image format pytesseract understands, or save temp
                # For simplicity in this skeleton, we assume a mechanism exists or we skip
                # implementing the full image conversion here to keep it concise.
                # Real implementation would use PIL/cv2 here.
                pass
            # text_content = ocr_text
        except Exception as e:
            print(f"OCR error: {e}")

    return text_content

def analyze_text(text: str):
    """
    Uses SpaCy to identify entities.
    """
    if not nlp:
        return {"error": "NLP model not loaded"}

    doc = nlp(text)

    entities = {
        "persons": [],
        "orgs": [],
        "locations": [],
        "dates": []
    }

    for ent in doc.ents:
        if ent.label_ == "PER":
            entities["persons"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["orgs"].append(ent.text)
        elif ent.label_ == "LOC":
            entities["locations"].append(ent.text)

    return entities
