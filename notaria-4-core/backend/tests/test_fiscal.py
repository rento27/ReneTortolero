import unittest
from decimal import Decimal
import sys
import os

# Add backend directory to path so we can import lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.fiscal_engine import FiscalEngine

class TestFiscalEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FiscalEngine()

    def test_persona_moral_detection(self):
        # 12 chars = Moral
        self.assertTrue(self.engine.is_persona_moral("ABC123456T1A"))
        # 13 chars = Fisica
        self.assertFalse(self.engine.is_persona_moral("ABCD123456T1A"))

    def test_tax_calculation_persona_fisica(self):
        # Subtotal: 1000
        # IVA 16%: 160
        # Retentions: 0
        result = self.engine.calculate_taxes(1000.00, is_persona_moral=False)
        self.assertEqual(result['subtotal'], 1000.00)
        self.assertEqual(result['iva_trasladado'], 160.00)
        self.assertEqual(result['ret_isr'], 0.00)
        self.assertEqual(result['ret_iva'], 0.00)

    def test_tax_calculation_persona_moral(self):
        # From the prompt example:
        # Base: 6083.91
        # ISR Ret (10%): 608.39
        # IVA Ret (10.6667% of Base OR 2/3 of IVA):
        # IVA = 6083.91 * 0.16 = 973.4256
        # Ret IVA = 973.4256 * 2 / 3 = 648.9504 -> 648.95

        base = 6083.91
        result = self.engine.calculate_taxes(base, is_persona_moral=True)

        self.assertEqual(result['subtotal'], 6083.91)
        # 6083.91 * 0.16 = 973.4256 -> 973.43
        self.assertEqual(result['iva_trasladado'], 973.43)

        # 6083.91 * 0.10 = 608.391 -> 608.39
        self.assertEqual(result['ret_isr'], 608.39)

        # 973.4256 * 2/3 = 648.9504 -> 648.95
        self.assertEqual(result['ret_iva'], 648.95)

    def test_isai_manzanillo(self):
        # Max(100, 200) * 0.03 = 200 * 0.03 = 6.00
        result = self.engine.calculate_isai_manzanillo(100.00, 200.00)
        self.assertEqual(result, 6.00)

if __name__ == '__main__':
    unittest.main()
