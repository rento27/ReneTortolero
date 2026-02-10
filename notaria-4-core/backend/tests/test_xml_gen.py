import unittest
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.xml_generator import XMLGenerator

class TestXMLGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = XMLGenerator(signer=None)

    def test_generate_structure(self):
        data = {
            "rfc": "XAXX010101000",
            "razon_social": "PUBLICO EN GENERAL",
            "monto": 1000.00,
            "escritura": "12345"
        }
        taxes = {
            "subtotal": 1000.00,
            "iva_trasladado": 160.00,
            "ret_isr": 0.00,
            "ret_iva": 0.00,
            "total_retentions": 0.00
        }

        cfdi = self.generator.generate_cfdi(data, taxes)

        # Verify basic attributes of the satcfdi Comprobante object (dictionary-like access)
        self.assertEqual(cfdi['Receptor']['Rfc'], "XAXX010101000")
        self.assertEqual(str(cfdi['Total']), "1160.00") # 1000 + 160

        # Verify Concept
        concept = cfdi['Conceptos'][0]
        self.assertIn("HONORARIOS NOTARIALES", concept['Descripcion'])

        # Verify Taxes in Concept
        # satcfdi automatically handles the lists
        traslado = concept['Impuestos']['Traslados'][0]
        # In satcfdi, decimal values might need string conversion for assertion or direct comparison
        # 1000 * 0.16 = 160.000000
        self.assertTrue(str(traslado['Importe']).startswith("160"))

if __name__ == '__main__':
    unittest.main()
