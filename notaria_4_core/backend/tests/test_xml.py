import sys
from unittest.mock import MagicMock
import unittest
from decimal import Decimal

# Mock satcfdi before it is imported by lib.xml_generator
mock_satcfdi = MagicMock()
sys.modules["satcfdi"] = mock_satcfdi
sys.modules["satcfdi.create"] = mock_satcfdi
sys.modules["satcfdi.create.cfd"] = mock_satcfdi

# Mock cfdi40.Comprobante behavior
mock_comprobante = MagicMock()
mock_satcfdi.cfdi40.Comprobante = mock_comprobante

# Now import the library
from lib.xml_generator import generar_xml, generar_complemento_notarios

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

        datos_notario = {
             "num_instrumento": "123",
             "fecha_instrumento": "2023-01-01",
             "monto_operacion": Decimal("100"),
             "subtotal": Decimal("10"),
             "iva": Decimal("1.6"),
             "calle": "Calle",
             "municipio": "Mun",
             "adquirientes": []
        }

        # Generate XML (Unsigned)
        # This will call the mocked Comprobante constructor
        cfdi = generar_xml(datos_factura, datos_notario)

        # Verify Comprobante was called
        mock_comprobante.assert_called()

        # Verify arguments passed to Comprobante
        call_args = mock_comprobante.call_args[1]
        self.assertEqual(call_args["emisor"]["Rfc"], "TOSR520601AZ4")

        # Verify complement was passed as a dict
        self.assertIn("complemento", call_args)
        self.assertEqual(call_args["complemento"]["DatosNotario"]["NumNotaria"], 4)

    def test_complemento_structure(self):
        data = {
            "num_instrumento": "23674",
            "fecha_instrumento": "2023-10-25",
            "monto_operacion": Decimal("1000000.00"),
            "subtotal": Decimal("10000.00"),
            "iva": Decimal("1600.00"),
            "calle": "AV. AUDIENCIA",
            "municipio": "MANZANILLO",
            "adquirientes": [
                {"nombre": "JUAN PEREZ", "rfc": "XAXX010101000", "porcentaje": Decimal("100.00")}
            ]
        }

        complemento = generar_complemento_notarios(data)

        self.assertEqual(complemento["DatosNotario"]["NumNotaria"], 4)
        self.assertEqual(complemento["DatosNotario"]["Adscripcion"], "MANZANILLO COLIMA")
        self.assertEqual(complemento["DatosOperacion"]["NumInstrumentoNotarial"], "23674")
        self.assertEqual(complemento["DatosAdquirientes"]["DatosAdquirientesCopSC"][0]["Porcentaje"], Decimal("100.00"))

if __name__ == '__main__':
    unittest.main()
