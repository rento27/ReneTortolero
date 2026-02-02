import unittest
from lib.fiscal_engine import FiscalEngine
from decimal import Decimal

class TestFiscalEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FiscalEngine()

    def test_sanitize_name(self):
        # Case 1: Standard SA DE CV
        raw = "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."
        expected = "INMOBILIARIA DEL PACÍFICO"
        self.assertEqual(self.engine.sanitize_name(raw), expected)

        # Case 2: No comma, mixed dots
        raw = "AGI BUILDING SYNERGY SA DE CV"
        expected = "AGI BUILDING SYNERGY"
        self.assertEqual(self.engine.sanitize_name(raw), expected)

        # Case 3: S.C.
        raw = "BUFETE JURIDICO SC"
        expected = "BUFETE JURIDICO"
        self.assertEqual(self.engine.sanitize_name(raw), expected)

    def test_calculate_taxes_persona_moral(self):
        # Scenario from prompt: Base $6,083.91
        # ISR Ret (10%): 608.39
        # IVA (16%): 973.4256
        # IVA Ret (2/3 of IVA): 648.9504 -> 648.95

        base = 6083.91
        result = self.engine.calculate_taxes(base, is_persona_moral=True)

        self.assertEqual(result['retencion_isr'], 608.39)
        self.assertEqual(result['retencion_iva'], 648.95)

        # Total check: 6083.91 + 973.43 (rounded IVA) - 608.39 - 648.95 = 5800.00
        # Let's check logic consistency
        # 6083.91 + 973.4256 - 608.391 - 648.9504 = 5800.00 (approx)

    def test_copropiedad_validation(self):
        # Exact 100
        self.assertTrue(self.engine.validate_copropiedad([50.00, 50.00]))
        # 99.9 Fail
        self.assertFalse(self.engine.validate_copropiedad([33.3, 33.3, 33.3]))
        # 100.1 Fail
        self.assertFalse(self.engine.validate_copropiedad([50.05, 50.05]))

    def test_calculate_isai(self):
        # Case 1: Price > Cadastral
        price = 1000000.00
        cadastral = 800000.00
        rate = 0.03 # 3%
        result = self.engine.calculate_isai(price, cadastral, rate)

        # Base should be 1,000,000
        # Tax should be 30,000
        self.assertEqual(result['base_isai'], 1000000.00)
        self.assertEqual(result['isai_total'], 30000.00)

        # Case 2: Cadastral > Price
        price = 500000.00
        cadastral = 600000.00
        result = self.engine.calculate_isai(price, cadastral, rate)

        self.assertEqual(result['base_isai'], 600000.00)
        self.assertEqual(result['isai_total'], 18000.00)

if __name__ == '__main__':
    unittest.main()
