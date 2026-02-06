import unittest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai_manzanillo, validate_copropiedad

class TestFiscalEngine(unittest.TestCase):
    def test_sanitize_name(self):
        self.assertEqual(sanitize_name("EMPRESA EJEMPLO S.A. DE C.V."), "EMPRESA EJEMPLO")
        self.assertEqual(sanitize_name("OTRA S.C."), "OTRA")
        self.assertEqual(sanitize_name("  ESPACIOS  S.A. "), "ESPACIOS")
        self.assertEqual(sanitize_name("SIN SUFIJO"), "SIN SUFIJO")

    def test_retentions_persona_moral(self):
        # RFC len 12 -> Moral
        subtotal = Decimal("1000.00")
        iva = Decimal("160.00")
        res = calculate_retentions("AAA010101AAA", subtotal, iva)

        self.assertTrue(res['is_persona_moral'])
        self.assertEqual(res['isr_amount'], Decimal("100.00")) # 10%
        # 160 * 2 / 3 = 106.6666... -> 106.67
        self.assertEqual(res['iva_amount'], Decimal("106.67"))

    def test_retentions_persona_fisica(self):
        # RFC len 13 -> Fisica
        res = calculate_retentions("AAAA010101AAA", Decimal("1000"), Decimal("160"))
        self.assertFalse(res['is_persona_moral'])
        self.assertEqual(res['isr_amount'], Decimal("0.00"))

    def test_isai(self):
        # Max(1M, 500k) * 3% = 30k
        res = calculate_isai_manzanillo(Decimal("1000000"), Decimal("500000"), Decimal("0.03"))
        self.assertEqual(res, Decimal("30000.00"))

    def test_copropiedad(self):
        self.assertTrue(validate_copropiedad([50.0, 50.0]))
        self.assertFalse(validate_copropiedad([50.0, 49.9]))
        self.assertFalse(validate_copropiedad([50.0, 50.1]))

if __name__ == '__main__':
    unittest.main()
