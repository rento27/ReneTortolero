import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from decimal import Decimal

# Try importing, if fails due to missing dependencies in this env, we skip
try:
    from lib.xml_generator import XMLGenerator
except ImportError:
    XMLGenerator = None

@pytest.mark.skipif(XMLGenerator is None, reason="satcfdi not installed")
def test_generate_cfdi_structure():
    # Mock data
    data = {
        "emisor": {
            "rfc": "TOSR520601AZ4",
            "nombre": "NOTARIA 4",
            "regimen_fiscal": "612",
            "lugar_expedicion": "28200"
        },
        "receptor": {
            "rfc": "ABC123456789", # Persona Moral
            "nombre": "EMPRESA CLIENTE, S.A. DE C.V.",
            "codigo_postal": "28200",
            "regimen_fiscal": "601",
            "uso_cfdi": "G03"
        },
        "conceptos": [
            {
                "clave_prod_serv": "84111506",
                "cantidad": 1,
                "clave_unidad": "E48",
                "unidad": "SERVICIO",
                "no_identificacion": "HON",
                "descripcion": "HONORARIOS",
                "valor_unitario": 1000.00,
                "importe": 1000.00,
                "objeto_imp": "02"
            }
        ],
        "notario_data": {
             "fecha_instrumento": "2023-10-27T12:00:00",
             "monto_operacion": 500000.00,
             "subtotal": 1000.00,
             "iva": 160.00,
             "adquirientes": []
        }
    }

    generator = XMLGenerator(signer=None)
    cfdi = generator.generate_cfdi(data)

    # Check basics
    assert cfdi["Receptor"]["Nombre"] == "EMPRESA CLIENTE"
    assert cfdi["Receptor"]["Rfc"] == "ABC123456789"

    # Check Retentions for Persona Moral
    conceptos = cfdi["Conceptos"]
    assert len(conceptos) == 1
    impuestos = conceptos[0]["Impuestos"]

    # Check if Retenciones exist
    assert "Retenciones" in impuestos
    retenciones = impuestos["Retenciones"]
    assert len(retenciones) == 2 # ISR and IVA
