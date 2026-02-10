import unittest
from unittest.mock import MagicMock, patch
import sys

# We need to make sure the module is imported
from lib.extraction_engine import ExtractionEngine

class TestExtractionEngine(unittest.TestCase):

    @patch('lib.extraction_engine.fitz')
    def test_extract_text_digital(self, mock_fitz):
        # Mock PyMuPDF behavior
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is a digital deed text that is long enough to bypass OCR trigger."

        # Correctly mock iteration over the document
        mock_doc.__iter__.return_value = iter([mock_page])

        mock_fitz.open.return_value = mock_doc

        engine = ExtractionEngine()
        text = engine.extract_text("dummy.pdf")

        # Check if fitz.open was called
        mock_fitz.open.assert_called_with("dummy.pdf")

        self.assertIn("digital deed", text)
        self.assertTrue(len(text) > 50)

    @patch('lib.extraction_engine.fitz')
    @patch('lib.extraction_engine.ExtractionEngine._extract_ocr')
    def test_fallback_to_ocr(self, mock_ocr, mock_fitz):
        # Mock PyMuPDF returning empty text (scanned doc)
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([]) # Empty doc
        mock_fitz.open.return_value = mock_doc

        mock_ocr.return_value = "OCR Result"

        engine = ExtractionEngine()
        text = engine.extract_text("scanned.pdf")

        self.assertEqual(text, "OCR Result")
        mock_ocr.assert_called_once()

    @patch('lib.extraction_engine.spacy')
    def test_extract_entities(self, mock_spacy):
        # Mock Spacy behavior
        mock_nlp = MagicMock()
        mock_doc = MagicMock()

        ent1 = MagicMock()
        ent1.text = "Juan Perez"
        ent1.label_ = "PERSON"

        ent2 = MagicMock()
        ent2.text = "Notaria 4"
        ent2.label_ = "ORG"

        mock_doc.ents = [ent1, ent2]
        mock_nlp.return_value = mock_doc

        # Setup the engine with the mocked nlp
        engine = ExtractionEngine()
        engine.nlp = mock_nlp

        entities = engine.extract_entities("Juan Perez fue a la Notaria 4")

        self.assertIn("Juan Perez", entities["PERSON"])
        self.assertIn("Notaria 4", entities["ORG"])

if __name__ == '__main__':
    unittest.main()
