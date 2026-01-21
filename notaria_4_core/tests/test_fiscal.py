import unittest
from decimal import Decimal
from backend.lib.fiscal_engine import FiscalEngine

class TestFiscalEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FiscalEngine()

    def test_sanitize_name(self):
        """Test removal of corporate regimes."""
        cases = [
            ("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.", "INMOBILIARIA DEL PACÍFICO"),
            ("EMPRESA X S.C.", "EMPRESA X"),
            ("CONSTRUCTORA Y, S.A.P.I. DE C.V.", "CONSTRUCTORA Y"),
            ("SIMPLE NAME", "SIMPLE NAME"),
            ("", ""),
        ]
        for raw, expected in cases:
            self.assertEqual(self.engine.sanitize_name(raw), expected)

    def test_persona_moral_retentions(self):
        """Test calculation of ISR and IVA retentions for RFC length 12."""
        # Case 1: Persona Moral (12 chars)
        rfc_moral = "ABC123456789"
        subtotal = Decimal("1000.00")

        rets = self.engine.calculate_retentions(subtotal, rfc_moral)

        self.assertTrue(rets["is_persona_moral"])
        # ISR 10% -> 100.00
        self.assertEqual(rets["isr_ret"], Decimal("100.00"))

        # IVA Ret = 1000 * 0.16 * (2/3)
        # 160 * 0.6666... = 106.666... -> 106.67
        self.assertEqual(rets["iva_ret"], Decimal("106.67"))

        # Case 2: Persona Física (13 chars)
        rfc_fisica = "ABCD123456789"
        rets_fisica = self.engine.calculate_retentions(subtotal, rfc_fisica)
        self.assertFalse(rets_fisica["is_persona_moral"])
        self.assertEqual(rets_fisica["isr_ret"], Decimal("0.00"))

    def test_isai_manzanillo(self):
        """Test ISAI calculation: Max(Price, Catastral) * 0.03"""
        price = Decimal("1000000.00") # 1 Million
        catastral = Decimal("500000.00") # 500k

        # Should use price (higher)
        expected = price * Decimal("0.03") # 30,000
        self.assertEqual(self.engine.calculate_isai(price, catastral), expected)

        # Case where catastral is higher
        price_low = Decimal("100.00")
        catastral_high = Decimal("10000.00")
        expected_high = catastral_high * Decimal("0.03") # 300
        self.assertEqual(self.engine.calculate_isai(price_low, catastral_high), expected_high)

    def test_copropiedad_sum(self):
        """Test validation of 100% sum."""
        valid_percents = [Decimal("50.00"), Decimal("50.00")]
        self.assertTrue(self.engine.validate_copropiedad(valid_percents))

        invalid_percents = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")] # 99.99
        self.assertFalse(self.engine.validate_copropiedad(invalid_percents))

if __name__ == '__main__':
    unittest.main()
