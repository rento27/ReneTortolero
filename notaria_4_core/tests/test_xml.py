import unittest
from decimal import Decimal
from unittest.mock import MagicMock
from lib.xml_generator import XMLGenerator

class TestXMLGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = XMLGenerator()

    def test_xml_generation_with_retentions_only_on_02(self):
        """
        Test that retentions are ONLY applied to ObjetoImp='02'.
        """
        invoice_data = {
            "receptor": {
                "rfc": "ABC123456789", # Moral
                "nombre": "EMPRESA MORAL",
                "cp": "28200",
                "regimen": "601",
                "uso_cfdi": "G03"
            },
            "subtotal": 1200.00,
            "total": 1200.00,
            "conceptos": [
                 {
                    "ClaveProdServ": "84111506",
                    "Cantidad": Decimal("1"),
                    "ClaveUnidad": "E48",
                    "Descripcion": "HONORARIOS (TAXABLE)",
                    "ValorUnitario": Decimal("1000.00"),
                    "Importe": Decimal("1000.00"),
                    "ObjetoImp": "02" # Target
                },
                {
                    "ClaveProdServ": "84111506",
                    "Cantidad": Decimal("1"),
                    "ClaveUnidad": "E48",
                    "Descripcion": "SUPLIDOS (NON-TAXABLE)",
                    "ValorUnitario": Decimal("200.00"),
                    "Importe": Decimal("200.00"),
                    "ObjetoImp": "01" # Should NOT have retentions
                }
            ],
            "retentions": {
                "is_persona_moral": True
            }
        }

        try:
            cfdi = self.generator.generar_xml(invoice_data)
            self.assertIsNotNone(cfdi)

            # Check First Concept (Taxable)
            c1 = cfdi["Conceptos"][0]
            self.assertIn("Impuestos", c1)
            self.assertIn("Retenciones", c1["Impuestos"])

            # Check Second Concept (Non-Taxable)
            c2 = cfdi["Conceptos"][1]
            # It might have Impuestos=None or empty dict depending on satcfdi internal processing
            if "Impuestos" in c2 and c2["Impuestos"]:
                 self.assertNotIn("Retenciones", c2["Impuestos"])

        except Exception as e:
            self.fail(f"XML generation failed: {e}")

if __name__ == '__main__':
    unittest.main()
