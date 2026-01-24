import unittest
from decimal import Decimal
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.xml_generator import generate_xml

class TestXMLLogic(unittest.TestCase):

    def test_mixed_taxability(self):
        # 1. Honorarios (Taxable) $1000
        # 2. Suplidos (Non-Taxable) $500
        conceptos = [
            {'Cantidad': Decimal("1.00"), 'Importe': Decimal("1000.00"), 'ObjetoImp': '02', 'ValorUnitario': Decimal("1000.00"), 'Descripcion': 'Honorarios', 'ClaveProdServ': '80121603', 'ClaveUnidad': 'E48'},
            {'Cantidad': Decimal("1.00"), 'Importe': Decimal("500.00"), 'ObjetoImp': '01', 'ValorUnitario': Decimal("500.00"), 'Descripcion': 'Gastos', 'ClaveProdServ': '80121603', 'ClaveUnidad': 'E48'}
        ]

        emisor = {'Rfc': 'TOSR520601AZ4', 'Nombre': 'NOTARIO', 'RegimenFiscal': '612'}
        receptor = {'Rfc': 'XAXX010101000', 'Nombre': 'CLIENTE', 'RegimenFiscal': '616', 'DomicilioFiscal': '28860', 'UsoCFDI': 'S01'}

        # We assume generate_xml constructs the object but we only care about internal calculations
        # that end up in the CFDI object.
        # Since I can't easily inspect the 'cfdi' object without serialization (unless I mock attributes),
        # I will inspect the dump if possible, or trust the execution doesn't crash and maybe check logic indirectly if possible.

        # Actually, let's just run it to ensure no errors in the new logic loop.
        cfdi = generate_xml(emisor, receptor, conceptos, "123")

        # Check SubTotal
        self.assertEqual(cfdi['SubTotal'], Decimal("1500.00"))

        # Check Impuestos.Traslados
        # Base Gravable should be 1000. IVA = 160.
        traslados = cfdi['Impuestos']['Traslados']
        self.assertEqual(len(traslados), 1)
        self.assertEqual(traslados[0]['Importe'], Decimal("160.00"))
        self.assertEqual(traslados[0]['Base'], Decimal("1000.00"))

        # Total should be 1500 + 160 = 1660
        self.assertEqual(cfdi['Total'], Decimal("1660.00"))

if __name__ == '__main__':
    unittest.main()
