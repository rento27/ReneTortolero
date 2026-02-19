import pytest
from decimal import Decimal
from lib.xml_generator import generate_signed_xml
import os

# Set MOCK_SIGNER for this test session if not set
os.environ["MOCK_SIGNER"] = "1"

def test_generate_xml_structure():
    data = {
        'receptor': {
            'rfc': 'XAXX010101000',
            'nombre': 'PUBLICO EN GENERAL',
            'uso_cfdi': 'S01',
            'domicilio_fiscal': '28200',
            'regimen_fiscal': '616'
        },
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': '1',
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS',
                'valor_unitario': '1000.00',
                'importe': '1000.00', # Will be ignored/recalc
                'objeto_imp': '02'
            }
        ],
        'subtotal': '1000.00',
        'total': '1160.00'
    }

    xml_bytes = generate_signed_xml(data)
    assert b"cfdi:Comprobante" in xml_bytes
