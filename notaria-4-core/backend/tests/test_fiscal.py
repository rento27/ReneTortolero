import unittest
from lib.fiscal_engine import calculate_isai, calculate_retentions, sanitize_name
from lib.xml_generator import validate_copropiedad

class TestFiscalEngine(unittest.TestCase):

    def test_isai_manzanillo(self):
        # Case 1: Price > Cadastral
        self.assertEqual(calculate_isai(1000000, 800000), 30000.0)
        # Case 2: Cadastral > Price
        self.assertEqual(calculate_isai(500000, 800000), 24000.0)

    def test_retentions_persona_moral(self):
        # RFC length 12 triggers retention
        rfc_pm = "ABC123456789"
        subtotal = 1000.00
        retentions = calculate_retentions(rfc_pm, subtotal)
        self.assertIsNotNone(retentions)
        self.assertEqual(retentions['isr'], 100.00)
        self.assertEqual(retentions['iva_ret'], 106.67)

    def test_no_retentions_persona_fisica(self):
        # RFC length 13 (Persona Fisica) -> No retention
        rfc_pf = "ABCD123456789"
        subtotal = 1000.00
        retentions = calculate_retentions(rfc_pf, subtotal)
        self.assertIsNone(retentions)

    def test_sanitize_name(self):
        self.assertEqual(sanitize_name("EMPRESA X, S.A. DE C.V."), "EMPRESA X")
        self.assertEqual(sanitize_name("GRUPO Y S.C."), "GRUPO Y")
        self.assertEqual(sanitize_name("INDIVIDUO Z"), "INDIVIDUO Z")

    def test_validate_copropiedad(self):
        self.assertTrue(validate_copropiedad([50.00, 50.00]))
        self.assertTrue(validate_copropiedad([33.33, 33.33, 33.34]))
        self.assertFalse(validate_copropiedad([33.33, 33.33, 33.33])) # 99.99
        self.assertFalse(validate_copropiedad([50.00, 50.10])) # 100.10

if __name__ == '__main__':
    unittest.main()
