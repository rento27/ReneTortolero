import sys
import os
import unittest
from decimal import Decimal

# Add backend to path so we can import lib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.fiscal_engine import calculate_isai_manzanillo, calculate_retentions_persona_moral, sanitize_name, validate_copropiedad

class TestFiscalEngine(unittest.TestCase):
    def test_sanitize_name(self):
        self.assertEqual(sanitize_name("INMOBILIARIA DEL PACIFICO, S.A. DE C.V."), "INMOBILIARIA DEL PACIFICO")
        self.assertEqual(sanitize_name("GRUPO CONSTRUCTOR S.A. DE C.V."), "GRUPO CONSTRUCTOR")
        self.assertEqual(sanitize_name("EMPRESA S.C."), "EMPRESA")
        self.assertEqual(sanitize_name("JUAN PEREZ"), "JUAN PEREZ")

    def test_isai_calculation(self):
        # Max(100000, 50000) * 0.03 = 100000 * 0.03 = 3000
        self.assertEqual(calculate_isai_manzanillo(Decimal('100000'), Decimal('50000')), Decimal('3000.00'))
        # Max(50000, 100000) * 0.03 = 100000 * 0.03 = 3000
        self.assertEqual(calculate_isai_manzanillo(Decimal('50000'), Decimal('100000')), Decimal('3000.00'))

    def test_retentions_persona_moral(self):
        subtotal = Decimal('1000.00')
        rets = calculate_retentions_persona_moral(subtotal, is_persona_moral=True)
        # ISR 10% = 100.00
        self.assertEqual(rets['ret_isr'], Decimal('100.00'))
        # IVA Trasladado = 160.00. Ret IVA = 160 * 2/3 = 106.6666666666
        # Expected value depends on rounding context in the function, let's check strict equality
        self.assertAlmostEqual(float(rets['ret_iva']), 106.666666666, places=4)

    def test_validate_copropiedad(self):
        self.assertTrue(validate_copropiedad([Decimal('50.00'), Decimal('50.00')]))
        self.assertFalse(validate_copropiedad([Decimal('50.00'), Decimal('49.99')]))

if __name__ == '__main__':
    unittest.main()
