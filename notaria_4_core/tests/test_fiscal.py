import unittest
from decimal import Decimal
from backend.lib.fiscal_engine import sanitize_name, calculate_taxes, calculate_isai, validate_copropiedad, validate_zip_code

class TestFiscalEngine(unittest.TestCase):

    def test_sanitize_name(self):
        # Case 1: Standard SA DE CV
        self.assertEqual(sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."), "INMOBILIARIA DEL PACIFICO")
        # Case 2: S.A.
        self.assertEqual(sanitize_name("EMPRESA EJEMPLO S.A."), "EMPRESA EJEMPLO")
        # Case 3: S.C.
        self.assertEqual(sanitize_name("SERVICIOS LEGALES S.C."), "SERVICIOS LEGALES")
        # Case 4: No regime
        self.assertEqual(sanitize_name("JUAN PEREZ"), "JUAN PEREZ")
        # Case 5: Messy spacing
        self.assertEqual(sanitize_name("  GRUPO   INDUSTRIAL   S.A. DE C.V.  "), "GRUPO INDUSTRIAL")
        # Case 6: Variations
        self.assertEqual(sanitize_name("CONSTRUCTORA X, SA DE CV"), "CONSTRUCTORA X")

    def test_calculate_taxes_persona_fisica(self):
        # RFC 13 chars
        subtotal = Decimal("1000.00")
        rfc = "XAXX010101000"
        result = calculate_taxes(subtotal, rfc)

        self.assertEqual(result["iva_trasladado"], Decimal("160.00"))
        self.assertEqual(result["total"], Decimal("1160.00"))
        self.assertEqual(len(result["retenciones"]), 0)

    def test_calculate_taxes_persona_moral(self):
        # RFC 12 chars
        subtotal = Decimal("6083.91") # Example from prompt
        rfc = "AAA010101AAA"
        result = calculate_taxes(subtotal, rfc)

        # Check IVA Trasladado (16%)
        # 6083.91 * 0.16 = 973.4256 -> 973.43
        self.assertEqual(result["iva_trasladado"], Decimal("973.43"))

        # Check Retentions
        # ISR (10%): 608.39
        isr = next(r for r in result["retenciones"] if r["impuesto_nombre"] == "ISR")
        self.assertEqual(isr["importe"], Decimal("608.39"))

        # IVA Ret (10.6667%): 6083.91 * 0.106667 = 648.9524 -> 648.95
        iva_ret = next(r for r in result["retenciones"] if r["impuesto_nombre"] == "IVA")
        self.assertEqual(iva_ret["importe"], Decimal("648.95"))

        # Total
        # 6083.91 + 973.43 - 608.39 - 648.95 = 5800.00
        expected_total = Decimal("6083.91") + Decimal("973.43") - Decimal("608.39") - Decimal("648.95")
        self.assertEqual(result["total"], expected_total)

    def test_calculate_isai(self):
        # Max(Price, Catastral) * 0.03
        price = Decimal("1000000.00")
        catastral = Decimal("800000.00")
        isai = calculate_isai(price, catastral)
        self.assertEqual(isai, Decimal("30000.00"))

        # Case where Catastral is higher
        price = Decimal("500000.00")
        catastral = Decimal("900000.00")
        isai = calculate_isai(price, catastral)
        self.assertEqual(isai, Decimal("27000.00"))

    def test_validate_copropiedad(self):
        self.assertTrue(validate_copropiedad([Decimal("50.00"), Decimal("50.00")]))
        self.assertTrue(validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]))
        self.assertFalse(validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.33")])) # 99.99
        self.assertFalse(validate_copropiedad([Decimal("50.1"), Decimal("50.0")]))

    def test_validate_zip_code(self):
        # Valid Colima
        self.assertTrue(validate_zip_code("28200", "06"))
        self.assertTrue(validate_zip_code("28860", "06"))

        # Invalid Colima (starts with 45 - Jalisco)
        self.assertFalse(validate_zip_code("45000", "06"))

        # Invalid Format
        self.assertFalse(validate_zip_code("2820", "06")) # Short
        self.assertFalse(validate_zip_code("ABCDE", "06"))

if __name__ == '__main__':
    unittest.main()
