import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.extraction_engine import ExtractionEngine

class TestExtractionEngine(unittest.TestCase):
    def setUp(self):
        # We mock spacy and fitz to run tests without heavy dependencies in this env
        self.engine = ExtractionEngine()
        # Override nlp with a mock if it failed to load or for strict testing
        if isinstance(self.engine.nlp, MagicMock):
             pass

    @patch('lib.extraction_engine.fitz')
    def test_extract_text_digital(self, mock_fitz):
        # Mock a PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # Make the mock text longer than 50 chars to avoid OCR fallback
        long_text = "This is a digital PDF content. " * 5
        mock_page.get_text.return_value = long_text
        mock_doc.__iter__.return_value = [mock_page]
        # Also mock len(doc)
        mock_doc.__len__.return_value = 1

        mock_fitz.open.return_value = mock_doc

        text = self.engine.extract_text_from_pdf(b"fake_pdf_bytes")
        self.assertIn("digital PDF content", text)

    def test_extract_entities_regex(self):
        # Text with RFC and Amount
        text = "El cliente es INMOBILIARIA DEL SUR SA DE CV con RFC ISU800101XYZ. El valor es $1,500,000.00 pesos. Escritura numero 4500."

        data = self.engine.extract_entities(text)

        self.assertEqual(data['rfc'], "ISU800101XYZ")
        self.assertEqual(data['escritura'], "4500")
        self.assertEqual(data['monto'], 1500000.00)

    # Note: Testing spaCy logic specifically requires the model, which might be absent.
    # We rely on the Regex fallback for the critical path in this test suite.

if __name__ == '__main__':
    unittest.main()
