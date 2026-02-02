import sys
from unittest.mock import MagicMock
import unittest

# Mock dependencies before import as they are not available in sandbox
sys.modules["fitz"] = MagicMock()
sys.modules["pytesseract"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()

from lib.extraction_engine import ExtractionEngine

class TestExtractionEngine(unittest.TestCase):
    def test_parse_entities_regex(self):
        engine = ExtractionEngine()
        text = """
        INSTRUMENTO NUMERO 12345
        EN LA CIUDAD DE MANZANILLO...
        RFC: TOSR520601AZ4
        OTRO RFC: XAXX010101000
        PRECIO: $1,500,000.00
        """

        entities = engine.parse_entities(text)

        # Check Escritura
        self.assertIn("12345", entities["numero_escritura"])

        # Check RFCs
        self.assertIn("TOSR520601AZ4", entities["rfcs"])
        self.assertIn("XAXX010101000", entities["rfcs"])

        # Check Monto
        # Regex captures the number part
        self.assertIn("1,500,000.00", entities["montos_detectados"])

if __name__ == '__main__':
    unittest.main()
