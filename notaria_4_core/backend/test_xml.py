import unittest
from decimal import Decimal
from lib.xml_generator import generar_complemento_notarios

class TestXMLGenerator(unittest.TestCase):

    def test_generar_complemento_notarios(self):
        datos_notario = {
            "fecha_firma": "2023-10-27",
            "numero_escritura": 12345,
            "monto_operacion": 1000000.00,
            "subtotal": 50000.00,
            "iva": 8000.00,
            "calle": "AV. AUDIENCIA"
        }

        complemento = generar_complemento_notarios(datos_notario)

        self.assertEqual(complemento["DatosNotario"]["NumNotaria"], 4)
        self.assertEqual(complemento["DatosNotario"]["EntidadFederativa"], "06")
        self.assertEqual(complemento["DatosOperacion"]["MontoOperacion"], Decimal("1000000.00"))
        self.assertEqual(complemento["DatosNotarial"]["DescInmuebles"]["Inmuebles"][0]["Calle"], "AV. AUDIENCIA")

if __name__ == '__main__':
    unittest.main()
