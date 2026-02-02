import unittest
from decimal import Decimal
from fiscal_engine import FiscalEngine

class TestFiscalEngine(unittest.TestCase):
    def test_sanitize_name(self):
        self.assertEqual(FiscalEngine.sanitize_name("INMOBILIARIA DEL PACIFICO, S.A. DE C.V."), "INMOBILIARIA DEL PACIFICO")
        self.assertEqual(FiscalEngine.sanitize_name("GRUPO CONSTRUCTOR, S.A."), "GRUPO CONSTRUCTOR")
        self.assertEqual(FiscalEngine.sanitize_name("SERVICIOS LEGALES S.C."), "SERVICIOS LEGALES")
        self.assertEqual(FiscalEngine.sanitize_name("EMPRESA SIMPLE"), "EMPRESA SIMPLE")
        self.assertEqual(FiscalEngine.sanitize_name(""), "")

    def test_calculate_retentions_persona_moral(self):
        # RFC length 12 triggers retention
        rfc_pm = "ABC123456789"
        amount = Decimal("1000.00")
        iva = Decimal("160.00")
        retentions = FiscalEngine.calculate_retentions(rfc_pm, amount, iva)

        self.assertEqual(retentions["isr_retention"], Decimal("100.00")) # 10%
        # 160 * 2/3 = 106.6666... -> 106.67
        self.assertEqual(retentions["iva_retention"], Decimal("106.67"))

    def test_calculate_retentions_persona_fisica(self):
        # RFC length 13 triggers NO retention
        rfc_pf = "ABCD123456789"
        amount = Decimal("1000.00")
        iva = Decimal("160.00")
        retentions = FiscalEngine.calculate_retentions(rfc_pf, amount, iva)

        self.assertEqual(retentions["isr_retention"], Decimal("0.00"))
        self.assertEqual(retentions["iva_retention"], Decimal("0.00"))

    def test_calculate_isai_manzanillo(self):
        # Max(100, 200) * 0.03 = 200 * 0.03 = 6.00
        price = Decimal("100000.00")
        catastral = Decimal("120000.00")
        tasa = Decimal("0.03")
        isai = FiscalEngine.calculate_isai_manzanillo(price, catastral, tasa)
        self.assertEqual(isai, Decimal("3600.00"))

    def test_validate_copropiedad(self):
        valid = [Decimal("50.00"), Decimal("50.00")]
        self.assertTrue(FiscalEngine.validate_copropiedad(valid))

        invalid_under = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")] # 99.99
        self.assertFalse(FiscalEngine.validate_copropiedad(invalid_under))

        invalid_over = [Decimal("50.00"), Decimal("50.01")]
        self.assertFalse(FiscalEngine.validate_copropiedad(invalid_over))

if __name__ == '__main__':
    unittest.main()
