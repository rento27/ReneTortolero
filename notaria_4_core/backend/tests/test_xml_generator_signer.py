import pytest
from unittest.mock import patch
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
import os

def test_generate_xml_no_signer():
    # If MOCK_SIGNER is not 1 and signer is None, it should raise ValueError
    if "MOCK_SIGNER" in os.environ:
        del os.environ["MOCK_SIGNER"]

    data = {
        'receptor': {
            'rfc': 'ABC123456T12',
            'nombre': 'EMPRESA SA DE CV',
            'uso_cfdi': 'G03',
            'domicilio_fiscal': '28200'
        },
        'subtotal': '1000.00',
        'total': '1053.33',
        'conceptos': [
            {
                'clave_prod_serv': '84111506',
                'cantidad': '1.00',
                'clave_unidad': 'E48',
                'descripcion': 'HONORARIOS NOTARIALES',
                'valor_unitario': '1000.00',
                'importe': '1000.00',
                'objeto_imp': '02'
            }
        ]
    }

    with patch("notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager", return_value=None):
        with pytest.raises(ValueError, match="Signer could not be loaded from Secret Manager."):
            generate_signed_xml(data)
