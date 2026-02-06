from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml

def test_generate_signed_xml_success():
    invoice_data = {
        'receptor': {
            'rfc': 'XAXX010101000',
            'nombre': 'PUBLICO EN GENERAL',
            'uso_cfdi': 'S01',
            'domicilio_fiscal': '28200'
        },
        'subtotal': Decimal('100.00'),
        'total': Decimal('116.00'), # With IVA? Or just 100? Let's assume 100 + 16
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': 1.00,
                'clave_unidad': 'E48',
                'descripcion': 'SERVICIOS DE FACTURACION',
                'valor_unitario': 100.00,
                'importe': 100.00,
                'objeto_imp': '02'
            }
        ]
    }

    # This should fail currently because of the API mismatch in xml_generator.py
    try:
        xml = generate_signed_xml(invoice_data)
        assert xml.startswith(b'<?xml')
    except TypeError as e:
        pytest.fail(f"API Error: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected Error: {e}")
