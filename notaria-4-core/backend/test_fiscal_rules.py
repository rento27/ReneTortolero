import unittest
import sys
import os

# Add the backend directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fiscal_rules import calculate_retentions, calculate_isai
from decimal import Decimal

class TestFiscalRules(unittest.TestCase):

    def test_persona_moral_retentions(self):
        # Case 1: Persona Moral (12 chars)
        # RFC: ABC123456789 (12 chars)
        # Subtotal: 1000.00
        # ISR: 1000 * 0.10 = 100.00
        # IVA: 1000 * 0.16 = 160.00
        # IVA Ret: (160 * 2) / 3 = 106.67

        rfc = "ABC123456789"
        subtotal = 1000.00
        result = calculate_retentions(rfc, subtotal)

        self.assertEqual(result['type'], "Persona Moral")
        self.assertEqual(result['retentions']['ISR_001'], 100.00)
        self.assertEqual(result['retentions']['IVA_002'], 106.67)
        self.assertAlmostEqual(result['total_retention'], 206.67)

    def test_persona_fisica_retentions(self):
        # Case 2: Persona Fisica (13 chars)
        rfc = "ABCD123456789"
        subtotal = 1000.00
        result = calculate_retentions(rfc, subtotal)

        self.assertEqual(result['type'], "Persona Fisica")
        self.assertIsNone(result['retentions'])
        self.assertEqual(result['total_retention'], 0.0)

    def test_isai_calculation(self):
        # Case 1: Precio > Valor Catastral
        # Precio: 2,000,000
        # Catastral: 1,500,000
        # Tasa: 0.03
        # Base: 2,000,000
        # Impuesto: 60,000

        result = calculate_isai(2000000, 1500000, 0.03)
        self.assertEqual(result['base_gravable'], 2000000)
        self.assertEqual(result['isai_total'], 60000.00)

        # Case 2: Valor Catastral > Precio
        result = calculate_isai(1000000, 1500000, 0.03)
        self.assertEqual(result['base_gravable'], 1500000)
        self.assertEqual(result['isai_total'], 45000.00)

if __name__ == '__main__':
    unittest.main()
