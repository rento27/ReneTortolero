import unittest
from decimal import Decimal
from backend.lib.xml_generator import generate_xml, generar_complemento_notarios

class TestXMLGenerator(unittest.TestCase):

    def test_generar_complemento_notarios_structure(self):
        data = {
            "num_notaria": 4,
            "entidad": "06",
            "adscripcion": "MANZANILLO COLIMA",
            "num_instrumento": 12345,
            "fecha_instrumento": "2025-01-01",
            "monto_operacion": "1000000.00",
            "inmuebles": [
                {
                    "calle": "AVENIDA DEL MAR 123",
                    "municipio": "MANZANILLO",
                    "estado": "COLIMA",
                    "cp": "28200"
                }
            ],
            "adquirientes": [
                {
                    "nombre": "JUAN PEREZ",
                    "rfc": "PEPJ800101XXX",
                    "es_copropiedad": True,
                    "porcentaje": "50.00"
                },
                {
                    "nombre": "MARIA LOPEZ",
                    "rfc": "LOMM850101XXX",
                    "es_copropiedad": True,
                    "porcentaje": "50.00"
                }
            ]
        }

        comp = generar_complemento_notarios(data)

        self.assertEqual(comp["Version"], "1.0")
        self.assertEqual(comp["DatosNotario"]["NumNotaria"], 4)
        self.assertEqual(comp["DatosOperacion"]["MontoOperacion"], Decimal("1000000.00"))

        # Check Inmuebles
        self.assertEqual(len(comp["DescInmuebles"]["DescInmueble"]), 1)
        self.assertEqual(comp["DescInmuebles"]["DescInmueble"][0]["Calle"], "AVENIDA DEL MAR 123")

        # Check Copropiedad
        adquirientes = comp["DatosAdquirientes"]["DatosAdquiriente"]
        self.assertEqual(len(adquirientes), 2)
        self.assertIn("DatosAdquirientesCopSC", adquirientes[0])
        self.assertEqual(adquirientes[0]["DatosAdquirientesCopSC"]["Porcentaje"], Decimal("50.00"))

    def test_generate_xml_structure(self):
        emisor = {"Rfc": "TOSR520601AZ4", "RegimenFiscal": "612", "Nombre": "RENE MANUEL TORTOLERO SANTILLANA"}
        receptor = {"Rfc": "XAXX010101000", "UsoCFDI": "G03", "Nombre": "PUBLICO EN GENERAL", "DomicilioFiscalReceptor": "28200", "RegimenFiscalReceptor": "616"}
        conceptos = [
            {
                "ClaveProdServ": "80121603",
                "Cantidad": Decimal("1"),
                "ClaveUnidad": "E48",
                "Descripcion": "HONORARIOS",
                "ValorUnitario": Decimal("1000.00"),
                "Importe": Decimal("1000.00"),
                "ObjetoImp": "02",
                "Impuestos": {
                    "Traslados": [
                        {"Base": Decimal("1000.00"), "Impuesto": "002", "TipoFactor": "Tasa", "TasaOCuota": Decimal("0.160000"), "Importe": Decimal("160.00")}
                    ]
                }
            }
        ]
        datos_notario = {"num_instrumento": 1}

        cfdi = generate_xml(emisor, receptor, conceptos, datos_notario)

        # Verify Basic CFDI attributes
        self.assertEqual(cfdi["Emisor"]["Rfc"], "TOSR520601AZ4")
        self.assertEqual(cfdi["Receptor"]["Rfc"], "XAXX010101000")

        # Verify Debug Complemento
        self.assertIsNotNone(cfdi._complemento_notarios_debug)
        self.assertEqual(cfdi._complemento_notarios_debug["DatosOperacion"]["NumInstrumentoNotarial"], 1)

if __name__ == '__main__':
    unittest.main()
