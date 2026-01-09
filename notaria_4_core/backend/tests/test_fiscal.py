import unittest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai_manzanillo, validate_copropiedad

class TestFiscalEngine(unittest.TestCase):

    def test_sanitize_name(self):
        self.assertEqual(sanitize_name("EMPRESA EJEMPLO S.A. DE C.V."), "EMPRESA EJEMPLO")
        self.assertEqual(sanitize_name("  OTRA EMPRESA, S.C.  "), "OTRA EMPRESA")
        self.assertEqual(sanitize_name("SIMPLE NAME"), "SIMPLE NAME")
        self.assertEqual(sanitize_name("GRUPO INMOBILIARIO S DE RL DE CV"), "GRUPO INMOBILIARIO")

    def test_retentions_persona_moral(self):
        # RFC length 12 -> Moral
        subtotal = Decimal("1000.00")
        rfc = "ABC123456789" # 12 chars
        results = calculate_retentions(subtotal, rfc)

        self.assertTrue(results["is_persona_moral"])
        self.assertEqual(results["isr_retention"], Decimal("100.00")) # 10%
        self.assertEqual(results["iva_retention"], Decimal("106.67")) # 10.6667% -> 106.667 -> 106.67

    def test_retentions_persona_fisica(self):
        # RFC length 13 -> Fisica
        subtotal = Decimal("1000.00")
        rfc = "ABCD123456789" # 13 chars
        results = calculate_retentions(subtotal, rfc)

        self.assertFalse(results["is_persona_moral"])
        self.assertEqual(results["total_retention"], Decimal("0.00"))

    def test_isai_manzanillo(self):
        # Max(100k, 50k) * 0.03 = 100k * 0.03 = 3000
        self.assertEqual(calculate_isai_manzanillo(Decimal("100000"), Decimal("50000")), Decimal("3000.00"))
        # Max(100k, 200k) * 0.03 = 200k * 0.03 = 6000
        self.assertEqual(calculate_isai_manzanillo(Decimal("100000"), Decimal("200000")), Decimal("6000.00"))

    def test_copropiedad_validation(self):
        # Exact 100%
        percentages = [Decimal("50.00"), Decimal("50.00")]
        self.assertTrue(validate_copropiedad(percentages))

        # Exact 100% with 3 parts
        percentages = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        self.assertTrue(validate_copropiedad(percentages))

        # 99.99% should fail
        percentages = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")]
        self.assertFalse(validate_copropiedad(percentages))

        # 100.01% should fail
        percentages = [Decimal("50.00"), Decimal("50.01")]
        self.assertFalse(validate_copropiedad(percentages))

if __name__ == '__main__':
    unittest.main()
