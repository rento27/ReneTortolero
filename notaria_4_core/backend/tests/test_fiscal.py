import unittest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_retentions, validate_copropiedad, calculate_isai

class TestFiscalEngine(unittest.TestCase):

    def test_sanitize_name(self):
        # Test Case 1: Standard SA de CV
        raw = "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."
        expected = "INMOBILIARIA DEL PACÍFICO"
        self.assertEqual(sanitize_name(raw), expected)

        # Test Case 2: S.C. with messy spacing
        raw = "BUFETE JURIDICO  , S.C. "
        expected = "BUFETE JURIDICO"
        self.assertEqual(sanitize_name(raw), expected)

        # Test Case 3: No regime
        raw = "JUAN PEREZ LOPEZ"
        expected = "JUAN PEREZ LOPEZ"
        self.assertEqual(sanitize_name(raw), expected)

    def test_retentions_persona_moral(self):
        # RFC Length 12 -> Moral
        rfc_moral = "AAA010101AAA"
        subtotal = Decimal("10000.00")

        result = calculate_retentions(rfc_moral, subtotal)

        self.assertTrue(result["is_persona_moral"])
        # ISR 10%
        self.assertEqual(result["retencion_isr"], Decimal("1000.00"))
        # IVA 10.6667% -> 1066.67
        self.assertEqual(result["retencion_iva"], Decimal("1066.67"))

    def test_retentions_persona_fisica(self):
        # RFC Length 13 -> Fisica
        rfc_fisica = "AAAA010101AAA"
        subtotal = Decimal("10000.00")

        result = calculate_retentions(rfc_fisica, subtotal)
        self.assertFalse(result["is_persona_moral"])
        self.assertEqual(result["retencion_isr"], Decimal("0.00"))

    def test_copropiedad_strict(self):
        # Exact 100%
        percentages = [Decimal("50.00"), Decimal("50.00")]
        self.assertTrue(validate_copropiedad(percentages))

        # 99.99% -> Fail
        percentages_fail = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")]
        self.assertFalse(validate_copropiedad(percentages_fail))

        # 100.00% with thirds (requires user to adjust manually to 33.34)
        percentages_manual_fix = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        self.assertTrue(validate_copropiedad(percentages_manual_fix))

    def test_isai_logic(self):
        # Max(Price, Catastral)
        price = Decimal("1000000.00")
        catastral = Decimal("1500000.00") # Higher
        tasa = Decimal("0.03")

        # Expected: 1.5M * 0.03 = 45,000
        expected = Decimal("45000.00")
        self.assertEqual(calculate_isai(price, catastral, tasa), expected)

if __name__ == '__main__':
    unittest.main()
