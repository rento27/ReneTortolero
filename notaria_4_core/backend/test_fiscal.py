import unittest
from decimal import Decimal
from lib.fiscal_engine import FiscalEngine

class TestFiscalEngine(unittest.TestCase):
    def test_sanitize_name(self):
        self.assertEqual(FiscalEngine.sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."), "INMOBILIARIA DEL PACÍFICO")
        self.assertEqual(FiscalEngine.sanitize_name("GRUPO MODELO S.A.B. DE C.V."), "GRUPO MODELO")
        self.assertEqual(FiscalEngine.sanitize_name("JUAN PEREZ"), "JUAN PEREZ")

    def test_calculate_retentions_pm(self):
        # Persona Moral (12 chars)
        subtotal = Decimal("6083.91")
        retentions = FiscalEngine.calculate_retentions(subtotal, "AGI8206015T2")

        # Expected: ISR 10% -> 608.39
        self.assertEqual(retentions['isr'], Decimal("608.39"))

        # Expected: IVA 10.6667% -> 6083.91 * 0.106667 = 648.9524 -> 648.95
        self.assertEqual(retentions['iva'], Decimal("648.95"))

    def test_calculate_retentions_pf(self):
        # Persona Fisica (13 chars)
        retentions = FiscalEngine.calculate_retentions(Decimal("1000.00"), "XAXX010101000")
        self.assertEqual(retentions, {})

    def test_calculate_isai(self):
        precio = Decimal("1000000.00")
        catastral = Decimal("800000.00")
        # Max is 1,000,000. 3% is 30,000.
        self.assertEqual(FiscalEngine.calculate_isai(precio, catastral), Decimal("30000.00"))

if __name__ == '__main__':
    unittest.main()
