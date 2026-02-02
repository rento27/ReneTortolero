import unittest
from decimal import Decimal
from satcfdi.create.cfd import cfdi40
from lib.xml_generator import generar_xml

class TestXMLGenerator(unittest.TestCase):

    def test_generar_xml_structure(self):
        # Mock Data
        datos_factura = {
            "emisor": {
                "Rfc": "TOSR520601AZ4",
                "Nombre": "RENE MANUEL TORTOLERO SANTILLANA",
                "RegimenFiscal": "612"
            },
            "receptor": {
                "Rfc": "XAXX010101000",
                "Nombre": "PUBLICO EN GENERAL",
                "UsoCFDI": "S01",
                "DomicilioFiscalReceptor": "28219",
                "RegimenFiscalReceptor": "616"
            },
            "conceptos": [
                {
                    "ClaveProdServ": "80121603",
                    "Cantidad": Decimal("1.00"),
                    "ClaveUnidad": "E48",
                    "Descripcion": "HONORARIOS NOTARIALES",
                    "ValorUnitario": Decimal("5000.00"),
                    "Importe": Decimal("5000.00"),
                    "ObjetoImp": "02",
                    "Impuestos": {
                        "Traslados": [
                            {"Base": Decimal("5000.00"), "Impuesto": "002", "TipoFactor": "Tasa", "TasaOCuota": Decimal("0.160000"), "Importe": Decimal("800.00")}
                        ]
                    }
                }
            ]
        }

        datos_notario = {} # Empty for now

        # Generate XML (Unsigned)
        cfdi = generar_xml(datos_factura, datos_notario)

        # Verify Object Type
        self.assertIsInstance(cfdi, cfdi40.Comprobante)

        # Verify Attributes
        self.assertEqual(cfdi["Emisor"]["Rfc"], "TOSR520601AZ4")
        self.assertEqual(cfdi["Total"], Decimal("5800.00")) # 5000 + 800

if __name__ == '__main__':
    unittest.main()
