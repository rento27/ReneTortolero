import os
import pytest
from decimal import Decimal
from notaria_4_core.backend.lib.xml_generator import generate_signed_xml
from unittest.mock import patch, MagicMock

@patch('notaria_4_core.backend.lib.xml_generator.load_signer_from_secret_manager')
@patch('notaria_4_core.backend.lib.xml_generator.cfdi40.Comprobante')
def test_generate_xml(mock_comprobante_class, mock_load_signer):
    mock_signer = MagicMock()
    mock_load_signer.return_value = mock_signer

    mock_comprobante = MagicMock()
    mock_comprobante.xml_bytes.return_value = b"<xml></xml>"
    mock_comprobante_class.return_value = mock_comprobante

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

    xml = generate_signed_xml(data)
    assert xml == b"<xml></xml>"
    mock_comprobante.sign.assert_called_once_with(mock_signer)
