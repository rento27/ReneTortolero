import unittest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai_manzanillo, validate_copropiedad, validate_zip_code

class TestFiscalEngine(unittest.TestCase):

    def test_sanitize_name(self):
        # Test stripping different regimes
        self.assertEqual(sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."), "INMOBILIARIA DEL PACIFICO")
        self.assertEqual(sanitize_name("CONSTRUCTORA X S.A DE C.V."), "CONSTRUCTORA X")
        self.assertEqual(sanitize_name("SERVICIOS PROFESIONALES S.C."), "SERVICIOS PROFESIONALES")
        self.assertEqual(sanitize_name("EMPRESA SA"), "EMPRESA")
        # Test punctuation removal
        self.assertEqual(sanitize_name("GRUPO INDUSTRIAL, INC."), "GRUPO INDUSTRIAL")
        # Test unicode normalization
        self.assertEqual(sanitize_name("JOSÉ PÉREZ GÓMEZ"), "JOSE PEREZ GOMEZ")
        self.assertEqual(sanitize_name("COMPAÑÍA DE LUZ"), "COMPANIA DE LUZ") # NFKD might split Ñ to N + ~, encode ASCII strips ~ -> COMPANIA. Valid for SAT usually.

    def test_calculate_retentions_persona_moral(self):
        # RFC 12 chars -> Persona Moral
        rfc = "ABC123456789"
        subtotal = Decimal("6083.91")
        iva = Decimal("973.43") # Approx 16%

        result = calculate_retentions(rfc, subtotal, iva)

        self.assertTrue(result['is_persona_moral'])
        # ISR 10% of 6083.91 = 608.391 -> 608.39
        self.assertEqual(result['isr_retention'], Decimal("608.39"))

        # IVA 2/3 of 973.43 = 648.9533 -> 648.95
        self.assertEqual(result['iva_retention'], Decimal("648.95"))

    def test_calculate_retentions_persona_fisica(self):
        # RFC 13 chars -> Persona Fisica
        rfc = "ABCD123456789"
        subtotal = Decimal("1000.00")
        iva = Decimal("160.00")

        result = calculate_retentions(rfc, subtotal, iva)

        self.assertFalse(result['is_persona_moral'])
        self.assertEqual(result['isr_retention'], Decimal("0.00"))
        self.assertEqual(result['iva_retention'], Decimal("0.00"))

    def test_calculate_isai_manzanillo(self):
        # ISAI = Max(Price, Catastral) * 0.03
        price = Decimal("1000000.00")
        catastral = Decimal("800000.00")
        # Base = 1,000,000 * 0.03 = 30,000
        self.assertEqual(calculate_isai_manzanillo(price, catastral), Decimal("30000.00"))

        # Case where Catastral is higher
        price = Decimal("500000.00")
        catastral = Decimal("900000.00")
        # Base = 900,000 * 0.03 = 27,000
        self.assertEqual(calculate_isai_manzanillo(price, catastral), Decimal("27000.00"))

    def test_validate_copropiedad(self):
        self.assertTrue(validate_copropiedad([Decimal("50.00"), Decimal("50.00")]))
        self.assertTrue(validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]))
        self.assertFalse(validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.33")])) # 99.99

if __name__ == '__main__':
    unittest.main()
