try:
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
    import io
except ImportError:
    # Allow import without dependencies for skeleton verification
    fitz = None
    pytesseract = None
    Image = None
    io = None

class ExtractionEngine:
    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        """
        Hybrid extraction: PyMuPDF for digital text, Tesseract for scanned images.
        """
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is not installed")

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            return f"Error opening PDF: {str(e)}"

        full_text = []

        for page in doc:
            # 1. Try digital extraction
            text = page.get_text()

            # 2. Heuristic: If text is sparse (< 50 chars), it might be a scan
            if len(text.strip()) < 50:
                try:
                    # Render page to image
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))

                    # Apply OCR
                    # lang='spa' for Spanish
                    ocr_text = pytesseract.image_to_string(image, lang='spa')
                    full_text.append(ocr_text)
                except Exception as e:
                    full_text.append(f"[OCR Failed: {str(e)}]")
            else:
                full_text.append(text)

        return "\n".join(full_text)
