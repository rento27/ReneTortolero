import unittest
from decimal import Decimal
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.fiscal_engine import calculate_isai, calculate_retentions, sanitize_name, validate_copropiedad

class TestFiscalEngine(unittest.TestCase):

    def test_sanitize_name(self):
        self.assertEqual(sanitize_name("INMOBILIARIA DEL PACIFICO, S.A. DE C.V."), "INMOBILIARIA DEL PACIFICO")
        self.assertEqual(sanitize_name("  GRUPO CONSTRUCTOR  S.A. DE C.V.  "), "GRUPO CONSTRUCTOR")
        self.assertEqual(sanitize_name("EMPRESA S.C."), "EMPRESA")
        self.assertEqual(sanitize_name("Juan Perez"), "JUAN PEREZ") # Uppercase

    def test_calculate_isai(self):
        # Case 1: Price > Cadastral
        # 1,000,000 * 0.03 = 30,000
        self.assertEqual(
            calculate_isai(Decimal("1000000.00"), Decimal("500000.00")),
            Decimal("30000.00")
        )

        # Case 2: Cadastral > Price
        # 800,000 * 0.03 = 24,000
        self.assertEqual(
            calculate_isai(Decimal("600000.00"), Decimal("800000.00")),
            Decimal("24000.00")
        )

    def test_calculate_retentions_moral(self):
        # RFC Persona Moral (12 chars)
        rfc = "ABC123456T1A"
        subtotal = Decimal("10000.00")

        ret = calculate_retentions(rfc, subtotal)

        self.assertTrue(ret["is_moral"])
        self.assertEqual(ret["ret_isr"], Decimal("1000.00")) # 10%
        # IVA: 10000 * 0.16 * (2/3) = 1600 * 0.66666... = 1066.67
        self.assertEqual(ret["ret_iva"], Decimal("1066.67"))

    def test_calculate_retentions_fisica(self):
        # RFC Persona Fisica (13 chars)
        rfc = "ABCD123456T1A"
        subtotal = Decimal("10000.00")

        ret = calculate_retentions(rfc, subtotal)

        self.assertFalse(ret["is_moral"])
        self.assertEqual(ret["ret_isr"], Decimal("0.00"))
        self.assertEqual(ret["ret_iva"], Decimal("0.00"))

    def test_validate_copropiedad(self):
        self.assertTrue(validate_copropiedad([Decimal("50.00"), Decimal("50.00")]))
        self.assertTrue(validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]))
        self.assertFalse(validate_copropiedad([Decimal("50.00"), Decimal("49.99")]))

if __name__ == '__main__':
    unittest.main()
