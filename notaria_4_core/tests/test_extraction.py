import unittest
from unittest.mock import MagicMock, patch
from backend.lib.extraction_engine import ExtractionEngine

class TestExtractionEngine(unittest.TestCase):

    @patch("backend.lib.extraction_engine.fitz.open")
    @patch("backend.lib.extraction_engine.pytesseract.image_to_string")
    def test_extract_text_digital(self, mock_ocr, mock_open):
        # Mock PyMuPDF doc
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # Text must be > 50 chars to avoid OCR fallback
        mock_page.get_text.return_value = "Texto digital suficiente para no usar OCR. " * 5
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        mock_open.return_value = mock_doc

        engine = ExtractionEngine()
        text = engine.extract_text("dummy.pdf")

        self.assertIn("Texto digital", text)
        mock_ocr.assert_not_called()

    @patch("backend.lib.extraction_engine.fitz.open")
    @patch("backend.lib.extraction_engine.pytesseract.image_to_string")
    def test_extract_text_scanned(self, mock_ocr, mock_open):
        # Mock PyMuPDF doc (sparse text)
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "   " # Too short

        # Configure pixmap mock with integer dimensions
        mock_pix = MagicMock()
        mock_pix.width = 100
        mock_pix.height = 100
        mock_pix.samples = b'\x00' * 30000
        mock_page.get_pixmap.return_value = mock_pix

        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        mock_open.return_value = mock_doc

        mock_ocr.return_value = "Texto escaneado OCR"

        engine = ExtractionEngine()
        text = engine.extract_text("dummy.pdf")

        self.assertIn("Texto escaneado OCR", text)
        mock_ocr.assert_called_once()

    def test_parse_entities(self):
        engine = ExtractionEngine()
        text = """
        ESCRITURA NÚMERO 12345
        EN LA CIUDAD DE MANZANILLO...
        RFC: TOSR520601AZ4
        PRECIO: $1,500,000.00
        """

        entities = engine.parse_entities(text)

        self.assertEqual(entities["numero_escritura"], "12345")
        self.assertIn("TOSR520601AZ4", entities["rfcs"])
        self.assertIn("$1,500,000.00", entities["montos"])

if __name__ == '__main__':
    unittest.main()
