from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

def test_generate_xml():
    data = {
        'receptor': {
            'rfc': 'ABC123456T12',
            'nombre': 'EMPRESA PRUEBA',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'subtotal': Decimal('1000.00'),
        'total': Decimal('1160.00'),
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': Decimal('1'),
                'clave_unidad': 'E48',
                'descripcion': 'Honorarios',
                'valor_unitario': Decimal('1000.00'),
                'importe': Decimal('1000.00'),
                'objeto_imp': '02'
            }
        ]
    }
    res = generate_signed_xml(data)
    assert res is not None
