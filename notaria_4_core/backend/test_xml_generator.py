import unittest
from decimal import Decimal
from lib.xml_generator import XMLGenerator
from satcfdi.create.cfd import cfdi40

class TestXMLGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = XMLGenerator(
            emisor_rfc="TOSR520601AZ4",
            emisor_name="RENE MANUEL TORTOLERO SANTILLANA",
            emisor_regimen="612",
            lugar_expedicion="28200"
        )

    def test_generate_xml_persona_fisica(self):
        # Persona Fisica (No Retentions)
        receptor = {
            "rfc": "XAXX010101000",
            "nombre": "PUBLICO EN GENERAL",
            "cp": "28200",
            "regimen_fiscal": "616",
            "uso_cfdi": "S01"
        }
        conceptos = [{
            "clave_prod_serv": "84111500",
            "cantidad": "1",
            "clave_unidad": "E48",
            "descripcion": "HONORARIOS NOTARIALES",
            "valor_unitario": Decimal("1000.00"),
            "amount": Decimal("1000.00")
        }]

        cfdi = self.generator.generar_xml(receptor, conceptos, Decimal("1000.00"), is_persona_moral=False)

        # Verify basic fields
        self.assertEqual(cfdi["Receptor"]["Rfc"], "XAXX010101000")
        self.assertEqual(cfdi["SubTotal"], Decimal("1000.00"))

        # Verify Taxes (Only Traslados)
        concept = cfdi["Conceptos"][0]
        self.assertTrue("Traslados" in concept["Impuestos"])
        self.assertFalse("Retenciones" in concept["Impuestos"])

    def test_generate_xml_persona_moral(self):
        # Persona Moral (With Retentions)
        receptor = {
            "rfc": "ABC121212ABC",
            "nombre": "EMPRESA DE PRUEBA", # Sanitized
            "cp": "28200",
            "regimen_fiscal": "601",
            "uso_cfdi": "G03"
        }
        conceptos = [{
            "clave_prod_serv": "84111500",
            "cantidad": "1",
            "clave_unidad": "E48",
            "descripcion": "HONORARIOS NOTARIALES",
            "valor_unitario": Decimal("6083.91"),
            "amount": Decimal("6083.91")
        }]

        cfdi = self.generator.generar_xml(receptor, conceptos, Decimal("6083.91"), is_persona_moral=True)

        concept = cfdi["Conceptos"][0]
        retenciones = concept["Impuestos"]["Retenciones"]

        # Check ISR (001) and IVA (002) Retentions
        has_isr = any(r["Impuesto"] == "001" for r in retenciones)
        has_iva = any(r["Impuesto"] == "002" for r in retenciones)

        self.assertTrue(has_isr)
        self.assertTrue(has_iva)

        # Verify IVA Rate 10.6667%
        iva_ret = next(r for r in retenciones if r["Impuesto"] == "002")
        self.assertEqual(iva_ret["TasaOCuota"], Decimal("0.106667"))

    def test_generar_complemento_notarios(self):
        datos_operacion = {
            "num_escritura": 12345,
            "fecha_inst_notarial": "2024-01-01",
            "monto_operacion": Decimal("1000000.00"),
            "inmuebles": [{
                "tipo": "03",
                "calle": "AVENIDA DEL MAR 1",
                "municipio": "MANZANILLO",
                "cp": "28200"
            }]
        }

        complemento = self.generator.generar_complemento_notarios(datos_operacion)

        self.assertEqual(complemento['DatosNotario']['NumNotaria'], 4)
        self.assertEqual(complemento['DatosNotario']['EntidadFederativa'], "06")
        self.assertEqual(complemento['DatosOperacion']['NumInstrumentoNotarial'], 12345)
        self.assertEqual(complemento['DescInmuebles']['DescInmueble'][0]['CodigoPostal'], "28200")

if __name__ == '__main__':
    unittest.main()
