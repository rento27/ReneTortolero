import unittest
from decimal import Decimal
from fiscal_engine import FiscalEngine

class TestFiscalEngine(unittest.TestCase):

    def test_sanitize_name(self):
        # Test Case 1: Standard S.A. DE C.V.
        raw = "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."
        expected = "INMOBILIARIA DEL PACÍFICO"
        self.assertEqual(FiscalEngine.sanitize_name(raw), expected)

        # Test Case 2: No suffix
        raw = "JUAN PEREZ LOPEZ"
        expected = "JUAN PEREZ LOPEZ"
        self.assertEqual(FiscalEngine.sanitize_name(raw), expected)

        # Test Case 3: S.C.
        raw = "BUFETE JURIDICO, S.C."
        expected = "BUFETE JURIDICO"
        self.assertEqual(FiscalEngine.sanitize_name(raw), expected)

        # Test Case 4: Extra spaces
        raw = "  EMPRESA   FANTASMA,   S.A.  "
        expected = "EMPRESA FANTASMA"
        self.assertEqual(FiscalEngine.sanitize_name(raw), expected)

    def test_persona_moral_retentions(self):
        # Scenario from prompt: Base $6,083.91
        # Receptor is Persona Moral (12 chars)
        base = Decimal('6083.91')
        rfc_moral = "ABC123456789" # 12 chars

        results = FiscalEngine.calculate_retentions(base, rfc_moral)

        self.assertTrue(results['is_persona_moral'])

        # ISR Check: 6083.91 * 0.10 = 608.391 -> 608.39
        self.assertEqual(results['isr_retention'], Decimal('608.39'))

        # IVA Retention Check:
        # IVA = 6083.91 * 0.16 = 973.4256
        # Ret = 973.4256 * (2/3) = 648.9504 -> 648.95
        self.assertEqual(results['iva_retention'], Decimal('648.95'))

    def test_persona_fisica_no_retention(self):
        base = Decimal('1000.00')
        rfc_fisica = "ABCD123456789" # 13 chars
        results = FiscalEngine.calculate_retentions(base, rfc_fisica)

        self.assertFalse(results['is_persona_moral'])
        self.assertEqual(results['isr_retention'], Decimal('0.00'))
        self.assertEqual(results['iva_retention'], Decimal('0.00'))

    def test_isai_manzanillo(self):
        # Max(1M, 500k) * 3%
        op_price = Decimal('1000000.00')
        cat_val = Decimal('500000.00')
        rate = Decimal('0.03')

        isai = FiscalEngine.calculate_isai_manzanillo(op_price, cat_val, rate)
        self.assertEqual(isai, Decimal('30000.00'))

        # Max(1M, 2M) * 3%
        cat_val_high = Decimal('2000000.00')
        isai = FiscalEngine.calculate_isai_manzanillo(op_price, cat_val_high, rate)
        self.assertEqual(isai, Decimal('60000.00'))

    def test_copropiedad(self):
        valid = [Decimal('50.00'), Decimal('50.00')]
        self.assertTrue(FiscalEngine.validate_copropiedad(valid))

        invalid = [Decimal('33.33'), Decimal('33.33'), Decimal('33.33')] # Sum 99.99
        self.assertFalse(FiscalEngine.validate_copropiedad(invalid))

if __name__ == '__main__':
    unittest.main()
